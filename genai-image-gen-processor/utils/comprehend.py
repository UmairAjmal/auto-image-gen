def is_prompt_positive(comprehend_client, prompt, LANGUAGE_CODE):
    print("Is prompt positive")
    response = comprehend_client.detect_sentiment(Text=prompt, LanguageCode=LANGUAGE_CODE)
    
    sentiment = response['Sentiment']
    score = response['SentimentScore']
    
    # Print the sentiment and score
    print('Sentiment:', sentiment)
    print('Score:', score)

    if sentiment.upper() in ('POSITIVE', 'NEUTRAL'):
        print("Prompt is Positive")
        return True
    else:
        print("Prompt is Negative")
        return False