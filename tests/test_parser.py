import textwrap

from app.m3u.parser import parse_m3u_content


class TestBasicParsing:
    def test_single_channel(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1 tvg-logo="http://example.com/logo.png" group-title="News",CNN
            http://stream.example.com/cnn
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 1
        assert channels[0]["name"] == "CNN"
        assert channels[0]["url"] == "http://stream.example.com/cnn"
        assert channels[0]["logo"] == "http://example.com/logo.png"
        assert channels[0]["group"] == "News"

    def test_multiple_channels(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1 group-title="Sports",ESPN
            http://stream.example.com/espn
            #EXTINF:-1 group-title="Movies",HBO
            http://stream.example.com/hbo
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 2
        assert channels[0]["name"] == "ESPN"
        assert channels[1]["name"] == "HBO"

    def test_channel_without_logo(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1 group-title="General",RTVE
            http://stream.example.com/rtve
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 1
        assert channels[0]["logo"] == ""

    def test_channel_without_group(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1,Canal Local
            http://stream.example.com/local
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 1
        assert channels[0]["group"] == "Sin categoría"


class TestDirectiveIgnored:
    def test_extvlcopt_ignored(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1 group-title="Sports",ESPN
            #EXTVLCOPT:http-user-agent=Mozilla/5.0
            http://stream.example.com/espn
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 1
        assert channels[0]["url"] == "http://stream.example.com/espn"

    def test_extgrp_ignored(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1 group-title="Movies",Netflix
            #EXTGRP:Premium
            http://stream.example.com/netflix
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 1
        assert channels[0]["url"] == "http://stream.example.com/netflix"

    def test_multiple_directives_between_extinf_and_url(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1 group-title="Sports",ESPN
            #EXTVLCOPT:http-user-agent=Mozilla/5.0
            #EXTGRP:Premium
            #EXTVLCOPT:http-referrer=http://example.com
            http://stream.example.com/espn
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 1
        assert channels[0]["url"] == "http://stream.example.com/espn"


class TestRelativeUrls:
    def test_relative_path_resolved(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1,Canal1
            streams/canal1.ts
        """)
        base = "http://example.com/playlist/m3u"
        channels = parse_m3u_content(content, base_url=base)

        assert channels[0]["url"] == "http://example.com/playlist/streams/canal1.ts"

    def test_absolute_url_not_modified(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1,Canal1
            http://other.example.com/canal1
        """)
        base = "http://example.com/playlist/m3u"
        channels = parse_m3u_content(content, base_url=base)

        assert channels[0]["url"] == "http://other.example.com/canal1"


class TestDuplicateRemoval:
    def test_duplicate_urls_removed(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1 group-title="News",CNN
            http://stream.example.com/cnn
            #EXTINF:-1 group-title="News",CNN HD
            http://stream.example.com/cnn
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 1
        assert channels[0]["name"] == "CNN"

    def test_different_urls_kept(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1,CNN
            http://stream.example.com/cnn-sd
            #EXTINF:-1,CNN HD
            http://stream.example.com/cnn-hd
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 2


class TestIncompleteEntries:
    def test_extinf_without_url_skipped(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1,Canal Huerfano
            #EXTINF:-1,Canal Siguiente
            http://stream.example.com/valid
        """)
        channels = parse_m3u_content(content)

        assert len(channels) == 1
        assert channels[0]["name"] == "Canal Siguiente"

    def test_empty_content(self):
        assert parse_m3u_content("") == []

    def test_only_directives(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1
            #EXTVLCOPT:something
        """)
        assert parse_m3u_content(content) == []


class TestEdgeCases:
    def test_name_with_commas(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1,Canal, Local, HD
            http://stream.example.com/canal
        """)
        channels = parse_m3u_content(content)

        assert channels[0]["name"] == "Canal, Local, HD"

    def test_single_quotes_in_attributes(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1 tvg-logo='http://example.com/logo.png' group-title='News',CNN
            http://stream.example.com/cnn
        """)
        channels = parse_m3u_content(content)

        assert channels[0]["logo"] == "http://example.com/logo.png"
        assert channels[0]["group"] == "News"

    def test_rtmp_url(self):
        content = textwrap.dedent("""\
            #EXTM3U
            #EXTINF:-1,Canal RTMP
            rtmp://stream.example.com/live/canal
        """)
        channels = parse_m3u_content(content)

        assert channels[0]["url"] == "rtmp://stream.example.com/live/canal"
