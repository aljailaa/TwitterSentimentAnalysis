
from secrets import Oauth_Secrets
import tweepy
from textblob import TextBlob
import json
import serial

def analyze(input_word):
    secrets = Oauth_Secrets()       
    auth = tweepy.OAuthHandler(secrets.consumer_key, secrets.consumer_secret)
    auth.set_access_token(secrets.access_token, secrets.access_token_secret)

    api = tweepy.API(auth)

    Num_tweets = 100
    Tweets = tweepy.Cursor(api.search, q=input_word).items(Num_tweets)
    negative,positive = (0.0,0.0)
    neg_count,pos_count = (0,0)
    neutral_count = 0

    for tweet in Tweets:
        # print tweet.text
        blob = TextBlob(tweet.text)
        if blob.sentiment.polarity < 0:         #Negative tweets
            negative += blob.sentiment.polarity
            neg_count += 1
        elif blob.sentiment.polarity == 0:      #Neutral tweets
            neutral_count += 1
        else:                                   #Positive tweets
            positive += blob.sentiment.polarity
            pos_count += 1
    return [['Category', 'Tweets crawled'],['Positive',pos_count]
            ,['Neutral',neutral_count],['Negative',neg_count]]




class MyStreamListener(tweepy.StreamListener):

    def __init__(self):
        super().__init__()
        self.neutral_count = 0;
        self.reset()
        self.ardu = serial.Serial("/dev/ttyACM0" ,9600)

    def on_status(self, status):
        print(status.text)

            # print tweet.text
        blob = TextBlob(status.text)
        if blob.sentiment.polarity < 0:  # Negative tweets
            self.negative += blob.sentiment.polarity
            self.neg_count += 1
            self.send_to_arduino("-")
        elif blob.sentiment.polarity == 0:  # Neutral tweets
            self.neutral_count += 1
            self.send_to_arduino("n")
        else:  # Positive tweets
            self.positive += blob.sentiment.polarity
            self.pos_count += 1
            self.send_to_arduino("+")

        self.total_tweets = self.total_tweets + 1

        #self.send_to_arduino(status.text)

        return self.return_value

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False

    def send_to_arduino(self, text):
        self.ardu.write(text.encode())

    def close_arduino(self):
        self.ardu.close()

    def reset(self):
        self.neutral_count = 0;
        self.negative, self.positive = (0.0, 0.0)
        self.neg_count, self.pos_count = (0, 0)
        self.return_value = True
        self.total_tweets = 0;


class StreamTweets:
    __instance = None

    def __init__(self, text):
        self.text = text;
        secrets = Oauth_Secrets()
        self.auth = tweepy.OAuthHandler(secrets.consumer_key, secrets.consumer_secret)
        self.auth.set_access_token(secrets.access_token, secrets.access_token_secret)
        self.myStreamListener = MyStreamListener()
        self.trending = []

        """ Virtually private constructor. """
        if StreamTweets.__instance is not None:
            raise Exception("This class is a singleton! Call the instance methods")
        else:
            StreamTweets.__instance = self

    def start_streaming(self):
        self.stop_streaming()
        self.myStreamListener.ardu = serial.Serial("/dev/ttyACM1" ,9600)
        self.myStreamListener.return_value = True
        myStream = tweepy.Stream(auth=self.auth, listener=self.myStreamListener)
        if "#" in self.text:
            myStream.filter(track=[self.text], languages=["en"])
        else:
            myStream.filter(track=["#" + self.text], languages=["en"], async=True)

    def stop_streaming(self):
        self.myStreamListener.return_value = False
        self.myStreamListener.close_arduino()


    def get_data(self):
        stream = self.myStreamListener
        if stream.total_tweets == 0:
            return [['Category', 'Tweets crawled'], ['Positive', 0],['Neutral', 0], ['Negative', 0]]

        return [['Category', 'Tweets crawled'], ['Positive', ((stream.pos_count / stream.total_tweets) * 100)]
                ,['Neutral', ((stream.neutral_count / stream.total_tweets) * 100)], ['Negative', ((stream.neg_count / stream.total_tweets) * 100)]]

    def get_trending(self):
        self.trending = []
        api = tweepy.API(self.auth)
        # Where On Earth ID for Brazil is 23424768.
        WOE_ID = 23424977

        brazil_trends = api.trends_place(WOE_ID)

        trends = json.loads(json.dumps(brazil_trends, indent=1))

        for trend in trends[0]["trends"]:
            self.trending.append(trend["name"])

        self.stop_streaming()
        self.text = self.trending[0].replace(" ", "")
        self.start_streaming()

    def get_trending_cache(self):
        return self.trending


    @staticmethod
    def get_instance(text = None):
        if StreamTweets.__instance is None:
            StreamTweets.__instance = StreamTweets(text)
        elif text != None:
            StreamTweets.__instance.myStreamListener.reset()
            StreamTweets.__instance.text = text

        return StreamTweets.__instance