import unittest
from rss import parse_feed, resolve_channel_id, relevant, merge_previous

class FeedTests(unittest.TestCase):
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

if __name__=='__main__':unittest.main()
