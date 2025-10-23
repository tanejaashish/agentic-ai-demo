"""
Text processing utilities for NLP tasks
"""

import re
import string
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """
    Utility class for text processing and NLP tasks
    """
    
    def __init__(self):
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with', 'the', 'this',
            'these', 'those', 'i', 'we', 'you', 'they', 'have', 'had'
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text
        """
        # Clean text
        cleaned = self.clean_text(text)
        
        # Split into words
        words = cleaned.split()
        
        # Remove stop words
        keywords = [
            word for word in words 
            if word not in self.stop_words and len(word) > 2
        ]
        
        # Count frequency
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(
            word_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [word for word, freq in sorted_keywords[:max_keywords]]
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[str]:
        """
        Split text into overlapping chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def extract_entities(self, text: str) -> dict:
        """
        Extract named entities from text (simplified)
        """
        entities = {
            "errors": [],
            "systems": [],
            "numbers": [],
            "urls": []
        }
        
        # Extract error-like patterns
        error_patterns = [
            r'Error:?\s*([^\n.]+)',
            r'Exception:?\s*([^\n.]+)',
            r'Failed:?\s*([^\n.]+)'
        ]
        for pattern in error_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["errors"].extend(matches)
        
        # Extract system names (simplified - look for capitalized words)
        words = text.split()
        for word in words:
            if word[0].isupper() and len(word) > 2 and word not in self.stop_words:
                entities["systems"].append(word)
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\.?\d*\b', text)
        entities["numbers"] = numbers
        
        # Extract URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        entities["urls"] = urls
        
        return entities
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity (Jaccard similarity)
        """
        # Clean and tokenize
        words1 = set(self.clean_text(text1).split())
        words2 = set(self.clean_text(text2).split())
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """
        Create a simple extractive summary
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return text[:max_length]
        
        # Score sentences by keyword frequency
        keywords = self.extract_keywords(text, 5)
        sentence_scores = []
        
        for sentence in sentences:
            score = sum(1 for keyword in keywords if keyword in sentence.lower())
            sentence_scores.append((sentence, score))
        
        # Sort by score and take top sentences
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        summary = []
        current_length = 0
        
        for sentence, score in sentence_scores:
            if current_length + len(sentence) <= max_length:
                summary.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        return '. '.join(summary) + '.' if summary else text[:max_length]