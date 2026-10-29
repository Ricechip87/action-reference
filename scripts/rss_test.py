import unittest
from rss import parse_feed, resolve_channel_id, relevant

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

if __name__=='__main__':unittest.main()
