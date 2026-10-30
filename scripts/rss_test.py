import unittest
import datetime as dt
from rss import parse_feed, resolve_channel_id, relevant, merge_previous, load_channel_entries, video_type
from channel_recent import parse_recent
from coverage import matches, person
from channel_archive import publication_window,collect_listing

class FeedTests(unittest.TestCase):
    def test_official_meet_the_crew_series_is_character_introduction(self):
        self.assertEqual(video_type('[EN]Granblue Fantasy: Relink | Meet the Crew: Gran'),'캐릭터 소개')

    def test_failed_rss_uses_only_verified_recent_grid_and_preserves_date_uncertainty(self):
        import json
        channel='UC'+'a'*22
        video={'lockupViewModel':{'contentId':'abcdefghijk','contentType':'LOCKUP_CONTENT_TYPE_VIDEO','metadata':{'lockupMetadataViewModel':{'title':{'content':'キャラ 全モーション集'},'metadata':{'contentMetadataViewModel':{'metadataRows':[{'metadataParts':[{'text':{'content':'1.8천'}},{'text':{'content':'11일 전'}}]}]}}}}}}
        data={'metadata':{'channelMetadataRenderer':{'externalId':channel,'title':'Uploader'}},'contents':{'twoColumnBrowseResultsRenderer':{'tabs':[{'tabRenderer':{'selected':True,'content':{'richGridRenderer':{'contents':[{'richItemRenderer':{'content':video}}]}}}}]}},'recommendation':{'videoRenderer':{'videoId':'badowner123'}}}
        page='var ytInitialData = '+json.dumps(data)+';';calls=[]
        def fetcher(url):
            calls.append(url)
            if '/feeds/' in url:raise OSError('RSS unavailable')
            return page
        entries,via,error=load_channel_entries(channel,fetcher)
        self.assertEqual([v['id'] for v in entries],['abcdefghijk'])
        self.assertEqual(entries[0]['publishedAt'],'')
        self.assertIn('publicationWindow',entries[0])
        self.assertEqual(via,'channel-videos');self.assertIn('RSS unavailable',error)
        self.assertEqual(load_channel_entries(channel,fetcher)[0],entries)
        self.assertEqual(len(calls),2)
        with self.assertRaises(ValueError):parse_recent(page,'UC'+'b'*22,dt.date(2026,10,30))

    def test_recent_fallback_keeps_known_exact_date_and_rejects_prelaunch_window(self):
        rule={'id':'ww','sourceKind':'creator','releaseDate':'2024-05-23','channelSpecific':True,'includeKeywords':['Showcase']}
        old={'id':'known','title':'Character Showcase','gameId':'ww','sourceChannel':'source','publishedAt':'2025-01-01T00:00:00Z'}
        fresh={**old,'publishedAt':'','publicationWindow':{'earliest':'2024-10-30','latest':'2025-10-30'}}
        self.assertEqual(merge_previous([fresh],[old],[(rule,'source')])[0]['publishedAt'],old['publishedAt'])
        self.assertFalse(relevant({**fresh,'publicationWindow':{'earliest':'2023-10-30','latest':'2024-10-30'}},rule))
    def test_reviewed_video_ids_do_not_relax_future_uploads_or_beta_filters(self):
        rule={'id':'gi','sourceKind':'creator','keywords':['Genshin Impact'],'includeKeywords':['All Skills'],'titleGameRequired':True,'requireCharacterMatch':True,'characterAliases':['Noelle'],'approvedVideoIds':['abcdefghijk'],'excludeKeywords':['CBT','all characters'],'releaseDate':'2020-09-28'}
        video={'id':'abcdefghijk','title':'Noelle blade animations','publishedAt':'2021-03-01T00:00:00Z'}
        self.assertTrue(relevant(video,rule))
        self.assertFalse(relevant({**video,'id':'newupload12'},rule))
        self.assertFalse(relevant({**video,'title':'Noelle CBT all characters'},rule))
        self.assertFalse(relevant({**video,'publishedAt':'2020-08-01T00:00:00Z'},rule))

    def test_rss_refresh_preserves_reviewed_scope_and_localized_title(self):
        rule={'id':'gi','sourceKind':'creator','channelSpecific':True,'includeKeywords':[]}
        old={'id':'abcdefghijk','gameId':'gi','sourceChannel':'@source','title':'old title','referenceScope':'basic-attacks','localizedTitles':['Noelle Attack Animations'],'verifiedAt':'2026-10-30','language':'ko'}
        current={k:old[k] for k in ['id','gameId','sourceChannel']};current.update(title='new title',language='')
        merged=merge_previous([current],[old],[(rule,'@source')])[0]
        self.assertEqual(merged['title'],'new title')
        self.assertEqual(merged['referenceScope'],'basic-attacks')
        self.assertEqual(merged['localizedTitles'],old['localizedTitles'])
        self.assertEqual(merged['language'],'ko')
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
        playlist=xml.replace('<title>Official</title>','<title>Playlist title</title><author><name>Actual uploader</name></author>')
        self.assertEqual(parse_feed(playlist,'UCKuq0c-RXYaulECSuu5hFug')[0]['channelTitle'],'Actual uploader')

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

    def test_reviewed_duplicate_exclusion_survives_feed_and_archive_refresh(self):
        rule={'keywords':['Genshin'],'includeKeywords':['animation'],'approvedVideoIds':['duplicate'],'excludedVideoIds':['duplicate']}
        duplicate={'id':'duplicate','title':'Hu Tao animation Genshin','gameId':'gi','sourceChannel':'source'}
        self.assertFalse(relevant(duplicate,rule))
        self.assertEqual(merge_previous([],[duplicate],[({**rule,'id':'gi'},'source')]),[])

    def test_expanded_channels_reject_unsafe_description_even_for_approved_id(self):
        rule={'keywords':['Genshin'],'approvedVideoIds':['reviewed'],'strictContentExclusions':True}
        for marker in ['beta footage','CBT2','leaks','private server','custom moveset','유출']:
            self.assertFalse(relevant({'id':'reviewed','title':'Character Skill Showcase Genshin','description':marker},rule))
        self.assertTrue(relevant({'id':'reviewed','title':'Character Skill Showcase Genshin','description':'Normal attacks, skill and burst'},rule))

    def test_japanese_no_leaks_statement_is_not_mistaken_for_leaked_footage(self):
        rule={'keywords':['Genshin'],'approvedVideoIds':['reviewed'],'strictContentExclusions':True}
        safe='公式より未発表のリーク情報や、テストサーバー等の機密情報は一切使用しておりません。'
        video={'id':'reviewed','title':'キャラ 全モーション集 Genshin','description':safe}
        self.assertTrue(relevant(video,rule))
        self.assertFalse(relevant({**video,'description':'ベータテスト映像'},rule))
        self.assertFalse(relevant({**video,'description':safe+'\nリーク映像を追加'},rule))

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

    def test_full_moveset_channel_promotional_clips_are_excluded(self):
        rule={'keywords':['Endfield'],'includeKeywords':['all Moveset'],'excludeKeywords':['公開中','投稿しました','鑑賞','本編にて'],'titleGameRequired':True}
        self.assertTrue(relevant({'title':'Laevatain all Moveset Gameplay | Endfield'},rule))
        for marker in rule['excludeKeywords']:
            self.assertFalse(relevant({'title':marker+' Laevatain all Moveset Gameplay | Endfield'},rule))

    def test_character_scoped_channel_can_omit_game_name_but_not_match_other_games(self):
        rule={'keywords':['NTE'],'includeKeywords':['Animations Showcase'],'requireCharacterMatch':True,'characterAliases':['Mint','Fadia']}
        self.assertTrue(relevant({'title':'Mint Animations Showcase','description':'NTE'},rule))
        self.assertFalse(relevant({'title':'Zoey Animations Showcase','description':'NTE and Tower of Fantasy'},rule))
        self.assertFalse(relevant({'title':'Minty Animations Showcase','description':'NTE'},rule))

    def test_unmarked_prelaunch_creator_video_is_excluded(self):
        rule={'sourceKind':'creator','channelSpecific':True,'releaseDate':'2024-07-04','includeKeywords':['Skill Showcase']}
        self.assertFalse(relevant({'title':'Grace Skill Showcase','publishedAt':'2024-06-17T10:00:00Z'},rule))
        self.assertTrue(relevant({'title':'Grace Skill Showcase','publishedAt':'2024-07-05T10:00:00Z'},rule))

if __name__=='__main__':unittest.main()
