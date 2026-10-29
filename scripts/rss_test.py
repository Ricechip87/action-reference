import unittest
import datetime as dt
from rss import parse_feed, resolve_channel_id, relevant, merge_previous
from coverage import matches, person
from channel_archive import publication_window,collect_listing

class FeedTests(unittest.TestCase):
    def test_relative_upload_window_is_conservative_and_never_an_exact_date(self):
        self.assertEqual(publication_window('3주 전',dt.date(2026,10,30))['earliest'],'2026-10-02')
        self.assertEqual(publication_window('5 months ago',dt.date(2026,10,30))['earliest'],'2026-04-30')
        self.assertIsNone(publication_window('date unknown',dt.date(2026,10,30)))

    def test_channel_listing_requires_matching_owner_and_rejects_beta(self):
        import json
        channel='UC'+'a'*22
        def item(id,title,label,owner=channel):return {'videoRenderer':{'videoId':id,'title':{'simpleText':title},'publishedTimeText':{'simpleText':label},'ownerText':{'runs':[{'navigationEndpoint':{'browseEndpoint':{'browseId':owner}}}]}}}
        payload={'metadata':{'channelMetadataRenderer':{'externalId':channel}},'items':[item('abcdefghijk','Endfield Skill Showcase','3주 전'),item('badowner123','Endfield Skill Showcase','3주 전','UC'+'b'*22),item('betavideo12','Endfield CBT Skill Showcase','3주 전'),item('oldvideo123','Endfield Skill Showcase','1년 전')]}
        rule={'id':'ef','sourceChannel':channel,'sourceKind':'creator','keywords':['Endfield'],'includeKeywords':['Skill Showcase'],'releaseDate':'2026-01-22','excludeKeywords':['CBT']}
        result=collect_listing(rule,channel,'skills',dt.date(2026,10,30),fetcher=lambda _: 'var ytInitialData = '+json.dumps(payload)+';')
        self.assertEqual([v['id'] for v in result],['abcdefghijk'])
        self.assertEqual(result[0]['publishedAt'],'')
    def test_feed_and_entities(self):
        xml='''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/"><title>Official</title><entry><yt:videoId>abcdefghijk</yt:videoId><yt:channelId>UCKuq0c-RXYaulECSuu5hFug</yt:channelId><title>Combat &amp; Trailer</title><published>2026-10-30T00:00:00Z</published><media:group><media:description>명조</media:description></media:group></entry></feed>'''
        v=parse_feed(xml,'UCKuq0c-RXYaulECSuu5hFug')[0]
        self.assertEqual(v['title'],'Combat & Trailer')
        self.assertEqual(v['description'],'명조')
        self.assertEqual(parse_feed(xml,'UC'+'x'*22),[])

    def test_channel_identity(self):
        channel='UCKuq0c-RXYaulECSuu5hFug'
        self.assertEqual(resolve_channel_id(channel,lambda _:''),channel)
        html=f'<link rel="canonical" href="https://www.youtube.com/channel/{channel}">'
        self.assertEqual(resolve_channel_id('@WW_KR_Official',lambda _:html),channel)
        with self.assertRaises(ValueError):resolve_channel_id('@bad',lambda _:'no channel')

    def test_purpose_filter(self):
        g={'keywords':['명조'],'includeKeywords':['전투 모션']}
        self.assertTrue(relevant({'title':'명조 전투 모션','description':''},g))
        self.assertFalse(relevant({'title':'명조 캐릭터 트레일러','description':''},g))
        self.assertFalse(relevant({'title':'다른 게임 트레일러','description':''},g))

    def test_archive_is_retained_without_age_limit_and_ids_are_unique(self):
        game={'id':'ww','channels':['@official'],'keywords':['명조'],'channelSpecific':True,'includeKeywords':['전투 모션']}
        old={'id':'old','gameId':'ww','sourceChannel':'@official','title':'공명자 전투 모션 | 과거','publishedAt':'2024-01-01T00:00:00Z'}
        new={**old,'id':'new','title':'공명자 전투 모션 | 신규'}
        result=merge_previous([new],[old,new],[(game,'@official')])
        self.assertEqual([v['id'] for v in result],['new','old'])
        self.assertEqual(merge_previous(result,[old,new],[(game,'@official')]),result)

    def test_nte_showcase_only(self):
        game={'id':'nte','keywords':['이환'],'channelSpecific':True,'includeKeywords':['캐릭터 쇼케이스']}
        self.assertTrue(relevant({'title':'이환 캐릭터 쇼케이스丨아카네 린'},game))
        self.assertTrue(relevant({'title':'캐릭터 쇼케이스 | 링코'},game))
        self.assertFalse(relevant({'title':'이환 캐릭터 PV | 아카네 린'},game))

    def test_zzz_character_play_only(self):
        game={'channelSpecific':True,'includeKeywords':['캐릭터 플레이']}
        self.assertTrue(relevant({'title':'피닉스 캐릭터 플레이 「죽지 마 도전」 | 젠레스 존 제로'},game))
        self.assertFalse(relevant({'title':'피닉스 캐릭터 PV | 젠레스 존 제로'},game))

    def test_creator_exclusions_and_compilations(self):
        game={'keywords':['Wuthering Waves'],'includeKeywords':['Skill Showcase'],'excludeKeywords':['leak','CBT','beta','all characters']}
        self.assertTrue(relevant({'title':'Changli Skill Showcase | Wuthering Waves'},game))
        for label in ['Leak','CBT','BETA','All Characters']:
            self.assertFalse(relevant({'title':label+' Skill Showcase | Wuthering Waves'},game))
        self.assertFalse(relevant({'title':'Jane Skill Showcase | Zenless Zone Zero'},game))

    def test_coverage_keeps_character_variants_separate(self):
        self.assertTrue(matches('Jane Doe Skill & Moveset Exhibition','제인',['Jane']))
        self.assertFalse(matches('Silver Soldier Anby Skill Showcase','엔비',['Anby']))
        self.assertFalse(matches('Starlight Billy Gameplay','빌리',['Billy']))
        self.assertEqual(person({'gameId':'neverness-to-everness','title':'이환 | 나나리 캐릭터 쇼케이스'}),'나나리')

    def test_new_game_character_names(self):
        self.assertEqual(person({'gameId':'genshin-impact','title':'원신 | 데인 여담-「스커크: 서늘한 세계의 고요함」'}),'스커크')
        self.assertEqual(person({'gameId':'arknights-endfield','title':'「명일방주: 엔드필드」 오퍼레이터 전투 시연 - 리노'}),'리노')
        self.assertEqual(person({'gameId':'punishing-gray-raven','title':'「아델라이드·파연」스킬 전시 #퍼니싱'}),'아델라이드·파연')

    def test_mixed_game_channels_require_game_name_in_title(self):
        rule={'keywords':['Neverness to Everness','NTE'],'titleGameRequired':True,'includeKeywords':['Gameplay']}
        self.assertFalse(relevant({'title':'Harly Painter Gameplay - Tower of Fantasy','description':'Also playing Neverness to Everness','gameVerified':True},rule))
        self.assertTrue(relevant({'title':'Akane Rin Gameplay | NTE'},rule))

    def test_unmarked_prelaunch_creator_video_is_excluded(self):
        rule={'sourceKind':'creator','channelSpecific':True,'releaseDate':'2024-07-04','includeKeywords':['Skill Showcase']}
        self.assertFalse(relevant({'title':'Grace Skill Showcase','publishedAt':'2024-06-17T10:00:00Z'},rule))
        self.assertTrue(relevant({'title':'Grace Skill Showcase','publishedAt':'2024-07-05T10:00:00Z'},rule))

if __name__=='__main__':unittest.main()
