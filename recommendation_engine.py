import pandas as pd
import re
from typing import Dict, List
from config import Config

class MilletRecommender:
    def __init__(self):
        self.df = pd.read_csv(Config.CSV_PATH)
        self.health_keywords = {
            'diabetes': ['diabet', 'sugar', 'blood sugar', 'glucose', 'glycemic', 'insulin'],
            'heart': ['heart', 'cholesterol', 'blood pressure', 'cardio', 'hypertension'],
            'digestive': ['digest', 'constipat', 'stomach', 'gut', 'bowel', 'fiber'],
            'anemia': ['anemia', 'iron', 'hemoglobin', 'blood', 'fatigue'],
            'weight': ['weight', 'obesity', 'diet', 'fat', 'slim', 'calorie'],
            'bones': ['bone', 'calcium', 'osteoporosis', 'fracture'],
            'gluten': ['gluten', 'celiac', 'allerg', 'intolerance']
        }

    def get_millet_stats(self, millet_type: str) -> Dict:
        """Get comprehensive statistics for a millet type"""
        millet_data = self.df[self.df['millet_type'] == millet_type]
        
        if millet_data.empty:
            return {}
        
        total_reviews = len(millet_data)
        avg_rating = millet_data['rating'].mean()
        
        sentiment_counts = millet_data['sentiment'].value_counts()
        positive_pct = (sentiment_counts.get('Positive', 0) / total_reviews) * 100
        
        # Get rating distribution
        rating_dist = millet_data['rating'].value_counts().sort_index().to_dict()
        
        return {
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 2),
            'positive_percentage': round(positive_pct, 1),
            'sentiment_distribution': sentiment_counts.to_dict(),
            'rating_distribution': rating_dist,
            'platform_distribution': millet_data['platform'].value_counts().to_dict()
        }

    def extract_common_themes(self, millet_type: str, health_concern: str) -> List[str]:
        """Extract common themes from reviews for specific health concerns"""
        millet_reviews = self.df[self.df['millet_type'] == millet_type]
        keywords = self.health_keywords.get(health_concern, [])
        
        themes = []
        for keyword in keywords:
            relevant_reviews = millet_reviews[millet_reviews['review'].str.contains(keyword, case=False, na=False)]
            if len(relevant_reviews) > 0:
                themes.append({
                    'theme': health_concern,
                    'keyword': keyword,
                    'count': len(relevant_reviews),
                    'avg_rating': relevant_reviews['rating'].mean(),
                    'sample_reviews': relevant_reviews.nlargest(2, 'rating')['review'].tolist()
                })
        
        return themes

    def get_sample_reviews(self, millet_type: str, sentiment: str = 'Positive', limit: int = 3) -> List[str]:
        """Get sample reviews for a millet type"""
        millet_reviews = self.df[
            (self.df['millet_type'] == millet_type) & 
            (self.df['sentiment'] == sentiment)
        ]
        
        if millet_reviews.empty:
            return ["No reviews available"]
        
        sample_reviews = millet_reviews.sample(min(limit, len(millet_reviews)))['review'].tolist()
        return [review[:150] + "..." if len(review) > 150 else review for review in sample_reviews]

    def calculate_millet_scores(self, health_concerns: List[str]) -> Dict[str, float]:
        """Calculate relevance scores for each millet based on health concerns"""
        scores = {}
        all_millets = self.df['millet_type'].unique()
        
        for millet in all_millets:
            score = 0
            millet_reviews = self.df[self.df['millet_type'] == millet]
            
            for concern in health_concerns:
                keywords = self.health_keywords.get(concern, [])
                concern_matches = 0
                
                for keyword in keywords:
                    matches = millet_reviews[millet_reviews['review'].str.contains(keyword, case=False, na=False)]
                    concern_matches += len(matches)
                
                # Normalize score based on total reviews
                if len(millet_reviews) > 0:
                    concern_score = (concern_matches / len(millet_reviews)) * 100
                    score += concern_score
            
            # Add average rating bonus
            avg_rating = millet_reviews['rating'].mean()
            score += (avg_rating - 3) * 10  # Bonus for higher ratings
            
            scores[millet] = round(score, 2)
        
        return scores

    def get_top_recommendations(self, health_concerns: List[str], top_n: int = 3) -> List[Dict]:
        """Get top millet recommendations with complete data"""
        scores = self.calculate_millet_scores(health_concerns)
        sorted_millets = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        recommendations = []
        for millet, score in sorted_millets:
            stats = self.get_millet_stats(millet)
            themes = []
            for concern in health_concerns:
                themes.extend(self.extract_common_themes(millet, concern))
            
            recommendations.append({
                'name': millet.title(),
                'score': score,
                'stats': stats,
                'themes': themes,
                'sample_reviews': self.get_sample_reviews(millet),
                'health_concern_match': self.get_health_concern_match(millet, health_concerns)
            })
        
        return recommendations

    def get_health_concern_match(self, millet_type: str, health_concerns: List[str]) -> Dict[str, float]:
        """Calculate match percentage for each health concern"""
        matches = {}
        millet_reviews = self.df[self.df['millet_type'] == millet_type]
        total_reviews = len(millet_reviews)
        
        if total_reviews == 0:
            return {concern: 0 for concern in health_concerns}
        
        for concern in health_concerns:
            keywords = self.health_keywords.get(concern, [])
            total_matches = 0
            
            for keyword in keywords:
                matches_count = len(millet_reviews[millet_reviews['review'].str.contains(keyword, case=False, na=False)])
                total_matches += matches_count
            
            match_percentage = (total_matches / total_reviews) * 100
            matches[concern] = round(match_percentage, 1)
        
        return matches