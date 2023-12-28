from constants import prompt_sentiment_values

def is_prompt_positive(comprehend_client, prompt, language_code):
    print("Is prompt positive")
    response = comprehend_client.detect_sentiment(Text=prompt, LanguageCode=language_code)
    
    sentiment = response['Sentiment']
    score = response['SentimentScore']
    
    # Print the sentiment and score
    print('Sentiment:', sentiment)
    print('Score:', score)

    if sentiment.upper() in prompt_sentiment_values:
        print("Prompt is Positive")
        return True
    else:
        print("Prompt is Negative")
        return False