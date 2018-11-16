from django.shortcuts import render
from django.http import HttpResponse
from main_app import analyze
# Create your views here.

def index(request):
    return HttpResponse("Welcome")

def home(request):
    if request.method == 'GET':
        data = {"template_var": "Inject templates here....!!", 'display_type': "none"}
        return render(request,"main_app/home.html",context=data)
    else:
        hashtag = request.POST["hashtag"]
        # data = analyze.analyze(hashtag)

        if request.POST.get("start"):
            print("Starting")
            streamTweets = analyze.StreamTweets.get_instance(hashtag)
            streamTweets.start_streaming()
        elif request.POST.get("stop"):
            print("Stopping")
            analyze.StreamTweets.get_instance().stop_streaming()
        elif request.POST.get("get_data"):
            print("Getting")
            # data example  [['Category', 'Tweets Crawled'], ['Positive', 18], ['Neutral', 23], ['Negative', 9]]
            # return render(request, "main_app/home.html",
            #               {'data': analyze.StreamTweets.get_instance().get_data(), 'hashtag': hashtag,
            #                'display_type': "block"})

        elif request.POST.get("get_trending"):
            analyze.StreamTweets.get_instance().get_trending()
            hashtag = analyze.StreamTweets.get_instance().text


        return render(request, "main_app/home.html",
                      {'data': analyze.StreamTweets.get_instance().get_data(), 'hashtag': hashtag,
                       'total': analyze.StreamTweets.get_instance().myStreamListener.total_tweets,
                       'trending': analyze.StreamTweets.get_instance().get_trending_cache(), 'display_type': "block"})




