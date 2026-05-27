"""SEO-specific prompt templates for AI content generation."""

# System prompt for SEO content writer
SEO_WRITER_SYSTEM = """You are an expert SEO content writer and digital marketing specialist.
Your job is to write high-quality, engaging, SEO-optimized content that ranks well in search engines.

Guidelines you ALWAYS follow:
- Write in a natural, human tone - avoid robotic or overly formal language
- Naturally incorporate target keywords without keyword stuffing (density 1-2%)
- Use proper heading hierarchy (H1, H2, H3) for content structure
- Write compelling introductions that hook readers
- Include relevant internal/external link suggestions
- Optimize for featured snippets where applicable
- Write meta titles (50-60 chars) and descriptions (150-160 chars)
- Use short paragraphs (2-3 sentences) for readability
- Include bullet points, numbered lists for scannable content
- Add a clear call-to-action where appropriate
- Ensure content is factually accurate and provides real value

Output format: Provide the article in clean Markdown format with proper headings."""

# Prompt templates
ARTICLE_PROMPT = """Write a comprehensive SEO-optimized article about the following topic:

**Topic:** {topic}
**Target Keyword:** {keyword}
**Secondary Keywords:** {secondary_keywords}
**Target Word Count:** {word_count} words
**Tone:** {tone}
**Target Audience:** {audience}
**Content Type:** {content_type}
**Language:** {language}

Additional instructions: {instructions}

Please write the full article with:
1. An SEO-optimized title (H1)
2. Meta title (50-60 characters)
3. Meta description (150-160 characters)
4. Well-structured content with H2/H3 subheadings
5. Natural keyword integration
6. A conclusion with CTA
"""

BLOG_POST_PROMPT = """Write a blog post optimized for SEO:

**Title/Topic:** {topic}
**Primary Keyword:** {keyword}
**Target Length:** {word_count} words
**Tone:** {tone} (conversational/professional/technical/casual)
**Target Audience:** {audience}
**Language:** {language}

Include:
- Engaging hook/introduction
- 3-5 main sections with H2 headings
- Practical tips or actionable advice
- Examples or case studies where relevant
- FAQ section (3-5 common questions)
- Conclusion with next steps

{instructions}"""

PRODUCT_DESCRIPTION_PROMPT = """Write an SEO-optimized product description:

**Product:** {topic}
**Target Keyword:** {keyword}
**Target Length:** {word_count} words
**Tone:** {tone}
**Audience:** {audience}
**Language:** {language}

Include:
- Compelling headline
- Key features and benefits
- Technical specifications (if applicable)
- Who it's for
- Why choose this product
- Call to action

{instructions}"""

META_TAGS_PROMPT = """Generate SEO-optimized meta tags for the following page:

**Page URL/Topic:** {topic}
**Primary Keyword:** {keyword}
**Secondary Keywords:** {secondary_keywords}
**Language:** {language}

Generate:
1. Meta Title (50-60 characters, include primary keyword near the start)
2. Meta Description (150-160 characters, compelling and keyword-rich)
3. H1 Tag suggestion
4. Open Graph Title
5. Open Graph Description
6. 5 variations of the meta title for A/B testing
"""

REWRITE_PROMPT = """Rewrite and SEO-optimize the following content:

**Original Content:**
{original_content}

**Target Keyword:** {keyword}
**Secondary Keywords:** {secondary_keywords}
**Target Tone:** {tone}
**Language:** {language}

Instructions:
- Improve readability (aim for Flesch score > 60)
- Add proper heading structure (H2, H3)
- Naturally integrate the target keyword (1-2% density)
- Make content more engaging and valuable
- Keep factual accuracy
- Improve meta tags
{instructions}"""

OUTLINE_PROMPT = """Create a detailed content outline for an SEO article:

**Topic:** {topic}
**Primary Keyword:** {keyword}
**Secondary Keywords:** {secondary_keywords}
**Target Length:** {word_count} words
**Audience:** {audience}
**Language:** {language}

Provide:
1. Suggested title (with keyword)
2. Meta description
3. Introduction approach
4. Detailed section outline (H2/H3) with key points per section
5. Suggested internal links
6. FAQ questions
7. CTA approach
8. Estimated word distribution per section

{instructions}"""

CONTENT_TYPES = {
    "article": ARTICLE_PROMPT,
    "blog_post": BLOG_POST_PROMPT,
    "product_description": PRODUCT_DESCRIPTION_PROMPT,
    "meta_tags": META_TAGS_PROMPT,
    "rewrite": REWRITE_PROMPT,
    "outline": OUTLINE_PROMPT,
}
