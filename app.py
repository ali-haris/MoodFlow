import streamlit as st
import requests
from openai import OpenAI
import time
import json
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="MoodFlow - Your Lifestyle Companion",
    page_icon="🧘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .mood-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    
    .recommendation-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .category-header {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        font-weight: bold;
        margin: 1rem 0 0.5rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .mood-emoji {
        font-size: 2rem;
        margin-right: 0.5rem;
    }
    
    .analysis-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: #333;
        margin: 1rem 0;
    }
    
    .dynamic-mapping-box {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: #333;
        margin: 1rem 0;
        border: 2px solid #e17055;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = {}
if 'current_mood' not in st.session_state:
    st.session_state.current_mood = ""
if 'mood_analysis' not in st.session_state:
    st.session_state.mood_analysis = {}
if 'ai_summary' not in st.session_state:
    st.session_state.ai_summary = ""
if 'dynamic_tags' not in st.session_state:
    st.session_state.dynamic_tags = {}


QLOO_API_KEY = st.secrets["QLOO_KEY"]
QLOO_BASE_URL = "https://hackathon.api.qloo.com/v2/insights"

OPENAI_API_KEY = st.secrets["OPENAI_KEY"]

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def get_available_qloo_tags():
    """Get a comprehensive list of available Qloo tags for dynamic mapping"""
    # This is a more comprehensive list of available Qloo tags
    # In a production environment, you might want to fetch this dynamically from Qloo API
    return {
        "movie_genres": [
            "urn:tag:genre:media:action", "urn:tag:genre:media:adventure", "urn:tag:genre:media:animation",
            "urn:tag:genre:media:biography", "urn:tag:genre:media:comedy", "urn:tag:genre:media:crime",
            "urn:tag:genre:media:documentary", "urn:tag:genre:media:drama", "urn:tag:genre:media:family",
            "urn:tag:genre:media:fantasy", "urn:tag:genre:media:film-noir", "urn:tag:genre:media:history",
            "urn:tag:genre:media:horror", "urn:tag:genre:media:music", "urn:tag:genre:media:musical",
            "urn:tag:genre:media:mystery", "urn:tag:genre:media:romance", "urn:tag:genre:media:sci-fi",
            "urn:tag:genre:media:sport", "urn:tag:genre:media:thriller", "urn:tag:genre:media:war",
            "urn:tag:genre:media:western", "urn:tag:genre:media:indie", "urn:tag:genre:media:cult"
        ],
        "music_genres": [
            "urn:tag:genre:music:pop", "urn:tag:genre:music:rock", "urn:tag:genre:music:hip-hop",
            "urn:tag:genre:music:jazz", "urn:tag:genre:music:classical", "urn:tag:genre:music:electronic",
            "urn:tag:genre:music:country", "urn:tag:genre:music:r&b", "urn:tag:genre:music:folk",
            "urn:tag:genre:music:reggae", "urn:tag:genre:music:blues", "urn:tag:genre:music:indie",
            "urn:tag:genre:music:ambient", "urn:tag:genre:music:punk", "urn:tag:genre:music:metal",
            "urn:tag:genre:music:alternative", "urn:tag:genre:music:funk", "urn:tag:genre:music:soul",
            "urn:tag:genre:music:world", "urn:tag:genre:music:acoustic", "urn:tag:genre:music:experimental"
        ],
        "book_categories": [
            "urn:tag:genre:media:fiction", "urn:tag:genre:media:non-fiction", "urn:tag:genre:media:biography",
            "urn:tag:genre:media:memoir", "urn:tag:genre:media:history", "urn:tag:genre:media:philosophy",
            "urn:tag:genre:media:science", "urn:tag:genre:media:self-help", "urn:tag:genre:media:psychology",
            "urn:tag:genre:media:poetry", "urn:tag:genre:media:mystery", "urn:tag:genre:media:romance",
            "urn:tag:genre:media:fantasy", "urn:tag:genre:media:sci-fi", "urn:tag:genre:media:thriller",
            "urn:tag:genre:media:adventure", "urn:tag:genre:media:business", "urn:tag:genre:media:health",
            "urn:tag:genre:media:spirituality", "urn:tag:genre:media:travel", "urn:tag:genre:media:cooking"
        ],
        "podcast_types": [
            "urn:tag:genre:media:comedy", "urn:tag:genre:media:education", "urn:tag:genre:media:news",
            "urn:tag:genre:media:storytelling", "urn:tag:genre:media:true-crime", "urn:tag:genre:media:business",
            "urn:tag:genre:media:health", "urn:tag:genre:media:technology", "urn:tag:genre:media:science",
            "urn:tag:genre:media:history", "urn:tag:genre:media:philosophy", "urn:tag:genre:media:motivation",
            "urn:tag:genre:media:mindfulness", "urn:tag:genre:media:interview", "urn:tag:genre:media:culture",
            "urn:tag:genre:media:politics", "urn:tag:genre:media:sports", "urn:tag:genre:media:arts"
        ],
        "destination_vibes": [
            "urn:tag:region:global:adventure", "urn:tag:region:global:relaxing", "urn:tag:region:global:cultural",
            "urn:tag:region:global:scenic", "urn:tag:region:global:urban", "urn:tag:region:global:quiet",
            "urn:tag:region:global:vibrant", "urn:tag:region:global:historic", "urn:tag:region:global:nature",
            "urn:tag:region:global:beach", "urn:tag:region:global:mountain", "urn:tag:region:global:tropical",
            "urn:tag:region:global:romantic", "urn:tag:region:global:family", "urn:tag:region:global:luxury",
            "urn:tag:region:global:budget", "urn:tag:region:global:exotic", "urn:tag:region:global:spiritual"
        ]
    }

def analyze_mood_and_generate_dynamic_tags(mood_description, time_context="", activity_preferences=None):
    """Use OpenAI to analyze mood and dynamically select the best Qloo tags"""
    try:
        activity_list = ", ".join(activity_preferences) if activity_preferences else "all content types"
        available_tags = get_available_qloo_tags()
        
        prompt = f"""
        MOOD TO ANALYZE: "{mood_description}"
        TIME CONTEXT: {time_context}
        USER INTERESTS: {activity_list}
        
        You are an expert mood analyst and content curator. Your job is to:
        1. Deeply analyze this person's emotional state and needs
        2. Select the MOST appropriate Qloo API tags from the available options
        3. Provide reasoning for your selections
        
        AVAILABLE QLOO TAGS:
        Movie Genres: {', '.join(available_tags['movie_genres'])}
        Music Genres: {', '.join(available_tags['music_genres'])}
        Book Categories: {', '.join(available_tags['book_categories'])}
        Podcast Types: {', '.join(available_tags['podcast_types'])}
        Destination Vibes: {', '.join(available_tags['destination_vibes'])}
        
        Based on the mood analysis, provide a JSON response with this structure:
        {{
            "mood_interpretation": "Empathetic interpretation of their emotional state and what they might need",
            "energy_level": "low/medium/high",
            "emotional_tone": "positive/negative/neutral/mixed/complex",
            "psychological_needs": "What this person psychologically needs right now (comfort, stimulation, escape, reflection, etc.)",
            "selected_tags": {{
                "movie": "exact tag from movie genres list that best matches their emotional needs",
                "music": "exact tag from music genres list that best matches their emotional needs", 
                "book": "exact tag from book categories list that best matches their emotional needs",
                "podcast": "exact tag from podcast types list that best matches their emotional needs",
                "destination": "exact tag from destination vibes list that best matches their emotional needs"
            }},
            "tag_reasoning": {{
                "movie": "Why this movie genre specifically matches their mood and psychological needs",
                "music": "Why this music genre specifically matches their mood and psychological needs",
                "book": "Why this book category specifically matches their mood and psychological needs", 
                "podcast": "Why this podcast type specifically matches their mood and psychological needs",
                "destination": "Why this destination vibe specifically matches their mood and psychological needs"
            }},
            "overall_strategy": "Brief explanation of the overall content strategy for this mood"
        }}
        
        IMPORTANT RULES:
        - Select tags that will genuinely help this person's current emotional state
        - Consider what they need psychologically (comfort vs stimulation, escapism vs reflection, etc.)
        - Use EXACT tag strings from the provided lists
        - Be specific and thoughtful in your reasoning
        - Consider how different content types work together to create a cohesive mood experience
        - Time context should influence selections (morning = energizing, evening = calming, etc.)
        """
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert psychologist and content curator who understands how different media affects human emotions and psychological states. You select content that genuinely helps people based on their current emotional needs."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4.1",
            max_tokens=800,
            temperature=0.7
        )
        
        # Parse the JSON response
        analysis = json.loads(response.choices[0].message.content.strip())
        return analysis
        
    except Exception as e:
        st.error(f"Error in dynamic mood analysis: {e}")
        # Fallback to safe defaults
        return {
            "mood_interpretation": f"Understanding your current state: {mood_description}",
            "energy_level": "medium",
            "emotional_tone": "mixed",
            "psychological_needs": "balance and comfort",
            "selected_tags": {
                "movie": "urn:tag:genre:media:drama",
                "music": "urn:tag:genre:music:indie", 
                "book": "urn:tag:genre:media:fiction",
                "podcast": "urn:tag:genre:media:storytelling",
                "destination": "urn:tag:region:global:scenic"
            },
            "tag_reasoning": {
                "movie": "Drama provides emotional depth and relatability",
                "music": "Indie music offers artistic authenticity and emotional nuance",
                "book": "Fiction allows for emotional exploration and escapism",
                "podcast": "Storytelling provides narrative engagement",
                "destination": "Scenic locations offer peaceful reflection opportunities"
            },
            "overall_strategy": "Providing balanced content for emotional equilibrium and gentle engagement."
        }

def get_qloo_recommendations(domain_type, tag):
    """Fetch recommendations from Qloo API"""
    try:
        response = requests.get(
            QLOO_BASE_URL,
            headers={"x-api-key": QLOO_API_KEY},
            params={
                "filter.type": f"urn:entity:{domain_type}",
                "filter.tags": tag
            }
        )
        
        if response.ok:
            data = response.json()
            entities = data.get("results", {}).get("entities", [])
            return entities[:4]  # Return top 4 recommendations
        else:
            st.error(f"Qloo API error for {domain_type}: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error fetching {domain_type} from Qloo: {e}")
        return []

def generate_final_summary(mood, mood_analysis, recommendations):
    """Generate a personalized final summary based on AI analysis"""
    try:
        rec_summary = []
        for category, items in recommendations.items():
            if items:
                rec_summary.append(f"{category.title()}: {', '.join([item.get('name', 'Unknown') for item in items[:2]])}")
        
        prompt = f"""
        USER'S ORIGINAL MOOD: "{mood}"
        AI MOOD INTERPRETATION: {mood_analysis.get('mood_interpretation', '')}
        PSYCHOLOGICAL NEEDS IDENTIFIED: {mood_analysis.get('psychological_needs', '')}
        OVERALL CONTENT STRATEGY: {mood_analysis.get('overall_strategy', '')}
        ACTUAL RECOMMENDATIONS FOUND: {'; '.join(rec_summary)}
        
        Create a warm, personalized, and psychologically insightful 3-4 sentence summary that:
        1. Acknowledges their specific emotional state with empathy
        2. Explains how this curated collection addresses their psychological needs
        3. Describes how the different content types work synergistically
        4. Provides encouraging words for their journey
        
        Make it feel like advice from a caring friend who truly understands their emotional state.
        """
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a compassionate lifestyle coach and emotional intelligence expert who creates deeply personalized, psychologically aware summaries that make people feel understood and cared for."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4.1",
            max_tokens=200,
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Your personalized content collection has been carefully curated to support your current emotional journey: {mood}. Each recommendation works together to provide exactly what you need right now. Trust the process and enjoy this thoughtfully designed experience!"

# Main App Interface
st.markdown("""
<div class="main-header">
    <h1>🧘 MoodFlow</h1>
    <h3>Your Personal Lifestyle Companion</h3>
    <p>Advanced AI-powered dynamic mood analysis for truly personalized content discovery</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for mood input
with st.sidebar:
    st.header("🎭 Describe Your Mood")
    
    # Main mood input
    user_mood = st.text_area(
        "How are you feeling right now?",
        placeholder="'I'm feeling emotionally drained. etc'",
        height=120
    )
    
    # Context inputs
    time_context = st.selectbox(
        "What time is it for you?",
        ["Morning", "Afternoon", "Evening", "Late Night"],
        help="This influences our AI's content strategy for your circadian rhythm"
    )
    
    # Activity preferences
    activity_preferences = st.multiselect(
        "What content types interest you?",
        ["Movies", "Music", "Books", "Podcasts", "Travel Ideas"],
        default=["Movies", "Books"]
    )
    
    # Additional context
    additional_context = st.text_input(
        "Any additional context? (optional)",
        placeholder="e.g., going through a breakup, just got promoted, feeling stuck creatively, preparing for a big decision..."
    )
    
    st.markdown("---")
    st.info("Our AI now dynamically understands your emotional needs and selects perfect content matches in real-time.")

# Main content area
if user_mood.strip():
    if st.button("✨ Find What I Need Right Now", key="analyze_mood"):
        with st.spinner("🧠 Understanding your emotional needs and finding perfect matches..."):
            
            # Combine mood with additional context
            full_mood_description = user_mood
            if additional_context:
                full_mood_description += f" Additional context: {additional_context}"
            
            # Step 1: AI Mood Analysis with Dynamic Tag Selection
            st.session_state.current_mood = user_mood
            mood_analysis = analyze_mood_and_generate_dynamic_tags(full_mood_description, time_context, activity_preferences)
            st.session_state.mood_analysis = mood_analysis
            st.session_state.dynamic_tags = mood_analysis.get('selected_tags', {})
            
            # Step 2: Fetch recommendations using AI-selected tags
            recommendations = {}
            domain_mapping = {
                "movie": "movie",
                "music": "artist", 
                "book": "book",
                "podcast": "podcast",
                "destination": "destination"
            }
            
            progress_bar = st.progress(0)
            total_domains = len(st.session_state.dynamic_tags)
            
            for i, (content_type, tag) in enumerate(st.session_state.dynamic_tags.items()):
                domain = domain_mapping.get(content_type)
                if domain and any(content_type in pref.lower().replace('s', '') for pref in activity_preferences):
                    recommendations[domain] = get_qloo_recommendations(domain, tag)
                    progress_bar.progress((i + 1) / total_domains)
                    time.sleep(0.3)  # Small delay for UX
            
            st.session_state.recommendations = recommendations
            
            # Step 3: Generate final summary
            final_summary = generate_final_summary(user_mood, mood_analysis, recommendations)
            st.session_state.ai_summary = final_summary
            
            progress_bar.empty()

# Display results
if st.session_state.get('mood_analysis') and st.session_state.get('current_mood'):
    
    # Display AI mood analysis
    analysis = st.session_state.mood_analysis
    st.markdown(f"""
    <div class="analysis-box">
        <h3><span class="mood-emoji">🎭</span>Understanding You</h3>
        <p><strong>"{st.session_state.current_mood}"</strong></p>
        <p><em>{analysis.get('mood_interpretation', '')}</em></p>
        <p><strong>What you need right now:</strong> {analysis.get('psychological_needs', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display content characteristics in a minimal, personal way
    if 'selected_tags' in analysis:
        chars = {}
        tag_reasoning = analysis.get('tag_reasoning', {})
        
        for content_type, tag in st.session_state.dynamic_tags.items():
            tag_name = tag.split(':')[-1].replace('-', ' ').title()
            chars[content_type] = tag_name
        
        st.markdown("### 🎯 Your Personal Content Profile")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if 'movie' in chars:
                st.metric("🎬 Movies", chars['movie'])
        with col2:
            if 'music' in chars:
                st.metric("🎵 Music", chars['music'])
        with col3:
            if 'book' in chars:
                st.metric("📚 Books", chars['book'])
        with col4:
            if 'podcast' in chars:
                st.metric("🎧 Podcasts", chars['podcast'])
        with col5:
            if 'destination' in chars:
                st.metric("✈️ Travel", chars['destination'])

# Display recommendations
if st.session_state.get('recommendations'):
    st.header("✨ Curated Just for You")
    
    # Create columns for better layout
    col1, col2 = st.columns(2)
    
    domain_names = {
        "movie": "Movies & Shows",
        "artist": "Music Artists", 
        "book": "Books",
        "podcast": "Podcasts",
        "destination": "Travel Destinations"
    }
    
    domain_emojis = {
        "movie": "🎬",
        "artist": "🎵", 
        "book": "📚",
        "podcast": "🎧",
        "destination": "✈️"
    }
    
    col_index = 0
    for domain, items in st.session_state.recommendations.items():
        current_col = col1 if col_index % 2 == 0 else col2
        
        with current_col:
            st.markdown(f"""
            <div class="category-header">
                {domain_emojis.get(domain, "🎯")} {domain_names.get(domain, domain.title())}
            </div>
            """, unsafe_allow_html=True)
            
            if items:
                for i, item in enumerate(items):
                    name = item.get('name', 'Unknown')
                    props = item.get('properties', {})
                    description = props.get('description', 'No description available')
                    image_url = props.get('image', {}).get('url', '') if 'image' in props else ''
                    
                    # Create clean recommendation card
                    card_html = f"""
                    <div class="recommendation-card">
                        <h4>{name}</h4>
                        <p style="color: #666; font-size: 0.9rem;">{description}</p>
                    """
                    
                    if image_url:
                        card_html += f'<img src="{image_url}" style="width:100%; max-width:180px; border-radius:8px; margin-top:8px;">'
                    
                    card_html += "</div>"
                    st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.info(f"No {domain} recommendations found for the AI-selected tags. The AI chose very specific criteria - try describing your mood with different nuances.")
        
        col_index += 1
    
    # Display AI-generated final summary
    if st.session_state.get('ai_summary'):
        st.markdown("---")
        st.markdown("### 💫 Your Personalized Journey")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); 
                    padding: 1.5rem; border-radius: 15px; color: #333; 
                    font-size: 1.1rem; line-height: 1.6; font-style: italic;">
            {st.session_state.ai_summary}
        </div>
        """, unsafe_allow_html=True)
        


# Instructions and help
if not user_mood.strip():
    st.markdown("### 🌟 How It Works")
    st.markdown("""
    **Tell me how you're feeling, and I'll understand what you need.**
    
    🧠 **AI analyzes your emotional state** - understanding your psychological needs  
    🎯 **Dynamic content selection** - choosing perfect matches from thousands of options  
    💫 **Personalized recommendations** - every mood gets a unique experience  
    
    **Try being specific:**
    - *"I'm overwhelmed and need something that helps me slow down and breathe"*
    - *"I'm celebrating but want to stay grounded and reflective"*  
    - *"I feel disconnected and want content that helps me feel understood"*
    - *"I'm anxious about tomorrow and need present-moment awareness"*
    
    The more you share, the better I understand what will truly help you.
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>✨ MoodFlow - Where AI meets emotional intelligence ✨</p>
    <p><small>Powered by advanced mood understanding and dynamic content curation</small></p>
</div>
""", unsafe_allow_html=True)