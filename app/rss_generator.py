"""
RSS Feed Generator - Creates valid RSS 2.0 XML with proper UTF-8 encoding
"""
from datetime import datetime
from email.utils import format_datetime
import html


def generate_rss_feed(
    title: str,
    link: str,
    description: str,
    items: list[dict],
    language: str = "uk"
) -> str:
    """Generate RSS 2.0 XML feed with proper UTF-8 encoding"""
    
    def escape_xml(text: str) -> str:
        """Escape XML special characters while preserving UTF-8"""
        if not text:
            return ""
        # Only escape XML special chars, keep UTF-8 as-is
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))
    
    def cdata(text: str) -> str:
        """Wrap text in CDATA section for complex content"""
        if not text:
            return ""
        # If text contains CDATA end marker, escape it
        text = text.replace("]]>", "]]]]><![CDATA[>")
        return f"<![CDATA[{text}]]>"
    
    last_build = format_datetime(datetime.now())
    
    # Build XML manually for proper encoding control
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">',
        '  <channel>',
        f'    <title>{escape_xml(title)}</title>',
        f'    <link>{escape_xml(link)}</link>',
        f'    <description>{escape_xml(description)}</description>',
        f'    <language>{language}</language>',
        f'    <lastBuildDate>{last_build}</lastBuildDate>',
        '    <generator>RSS Aggregator v1.0</generator>',
        f'    <atom:link href="{escape_xml(link)}" rel="self" type="application/rss+xml"/>',
    ]
    
    for item_data in items:
        item_title = item_data.get('title', '')
        item_link = item_data.get('link', '')
        item_desc = item_data.get('description', '')
        item_guid = item_data.get('guid', item_link)
        item_author = item_data.get('author', '')
        
        if item_data.get('source_name'):
            item_desc = f"[{item_data['source_name']}] {item_desc}"
        
        pub_date = item_data.get('pub_date')
        pub_date_str = ""
        if pub_date:
            if isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                except:
                    pub_date = datetime.now()
            pub_date_str = format_datetime(pub_date)
        
        xml_parts.append('    <item>')
        xml_parts.append(f'      <title>{cdata(item_title)}</title>')
        xml_parts.append(f'      <link>{escape_xml(item_link)}</link>')
        xml_parts.append(f'      <description>{cdata(item_desc)}</description>')
        xml_parts.append(f'      <guid isPermaLink="false">{escape_xml(item_guid)}</guid>')
        
        if pub_date_str:
            xml_parts.append(f'      <pubDate>{pub_date_str}</pubDate>')
        
        if item_author:
            xml_parts.append(f'      <dc:creator>{cdata(item_author)}</dc:creator>')
        
        xml_parts.append('    </item>')
    
    xml_parts.append('  </channel>')
    xml_parts.append('</rss>')
    
    return '\n'.join(xml_parts)

