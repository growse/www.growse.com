import datetime
import zlib
import cPickle
from decimal import Decimal

from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
import re
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count
from django.http import HttpResponsePermanentRedirect, HttpResponse, Http404
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from growse_com.blog.models import Article, Location
from growse_com.blog.models import Comment
import simplejson as json


def article_shorttitle(request, article_shorttitle=''):
    thisarticle = get_object_or_404(Article, shorttitle=article_shorttitle)
    articledate = thisarticle.datestamp.date()
    return HttpResponsePermanentRedirect(
        '/' + str(articledate.year) + '/' + str(articledate.month).zfill(2) + '/' + str(
            articledate.day).zfill(2) + '/' + thisarticle.shorttitle + '/')


def article_bydate(request, year, month='', day=''):
    thisarticle = None
    if day and month and year:
        try:
            thisarticle = Article.objects.filter(
                datestamp__year=year,
                datestamp__month=month,
                datestamp__day=day).order_by('datestamp')[0]
        except IndexError:
            raise Http404
    elif month and year:
        try:
            thisarticle = Article.objects.filter(datestamp__year=year, datestamp__month=month).order_by('datestamp')[0]
        except IndexError:
            raise Http404
    elif year:
        try:
            thisarticle = Article.objects.filter(datestamp__year=year).order_by('datestamp')[0]
        except IndexError:
            raise Http404

    if thisarticle:
        articledate = thisarticle.datestamp.date()
        return redirect('/' + str(articledate.year) + '/' + str(articledate.month).zfill(2) + '/' + str(
            articledate.day).zfill(2) + '/' + thisarticle.shorttitle + '/')


def navlist(request, direction, datestamp):
    if direction == 'before':
        articles = Article.objects.extra(where=['date_trunc(\'second\',datestamp)<%s'], params=[datestamp]).order_by(
            '-datestamp')
    elif direction == 'since':
        articles = Article.objects.extra(where=['date_trunc(\'second\',datestamp)>%s'], params=[datestamp]).order_by(
            'datestamp')
    response_data = []
    for article in articles:
        response_data.append({
            'title': article.title,
            'id': article.id,
            'shorttitle': article.shorttitle,
            'datestamp': article.datestamp.isoformat(),
            'year': str(article.datestamp.year).zfill(4) if article.datestamp else None,
            'month': str(article.datestamp.month).zfill(2) if article.datestamp else None,
            'day': str(article.datestamp.day).zfill(2) if article.datestamp else None
        })
    return HttpResponse(json.dumps(response_data), content_type='application/json')


def article(request, article_shorttitle=''):
    if article_shorttitle == '':
        article = Article.objects.filter(datestamp__isnull=False).latest('datestamp')
    else:
        article = get_object_or_404(Article, shorttitle=article_shorttitle)
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        website = request.POST.get('website')
        comment = request.POST.get('comment').strip()
        spamfilter = request.POST.get('email')
        articledate = article.datestamp.date()
        if (spamfilter is None or len(spamfilter) == 0) and len(comment) > 0 and len(name) > 0:
            Comment.objects.create(name=name, website=website, comment=comment, article=article,
                                   ip=request.META['REMOTE_ADDR'])
            send_mail('New Comment on growse.com',
                      'Someone posted a comment on growse.com. Over at http://www.growse.com/' + str(
                          articledate.year) + '/' + str(articledate.month).zfill(2) + '/' + str(
                          articledate.day).zfill(2) + '/' + article.shorttitle + '/',
                      'blog@growse.com', ['comments@growse.com'], fail_silently=False)

        return redirect('/' + str(articledate.year) + '/' + str(articledate.month).zfill(2) + '/' + str(
            articledate.day).zfill(2) + '/' + article.shorttitle + '/')
    else:
        pickled_navitems = cache.get('navitems')
        if pickled_navitems is None:
            navitems = Article.objects.filter(datestamp__isnull=False).order_by("-datestamp").all()
            pickled = zlib.compress(cPickle.dumps(navitems, cPickle.HIGHEST_PROTOCOL), 9)
            cache.set('navitems', pickled, None)
        else:
            navitems = cPickle.loads(zlib.decompress(pickled_navitems))

        comments = Comment.objects.filter(article__id=article.id).order_by("datestamp")

        pickled_archives = cache.get('archives')
        if pickled_archives is None:
            archives = Article.objects.filter(datestamp__isnull=False).extra(
                select={'month': "DATE_TRUNC('month',datestamp)"}).values(
                'month').annotate(Count('title')).order_by('-month')

            prevyear = None
            for archive in archives:
                if archive["month"].year != prevyear:
                    archive["newyear"] = True
                    prevyear = archive["month"].year
            pickled = zlib.compress(cPickle.dumps(archives, cPickle.HIGHEST_PROTOCOL), 9)
            cache.set('archives', pickled, None)
        else:
            archives = cPickle.loads(zlib.decompress(pickled_archives))
        lastlocation = Location.get_latest()
        return render(request, 'article.html',
                      {'archives': archives, 'navitems': navitems, 'comments': comments,
                       'article': article, 'lastlocation': lastlocation})


def search(request, searchterm=None, page=1):
    if searchterm is None:
        if request.method == 'GET':
            return redirect("/", Permanent=True)
        if request.method == 'POST':
            return redirect("/search/" + request.POST.get('a', '') + "/")
    else:
        results_list = Article.objects.extra(select={
            'rank': "ts_rank(idxfti,plainto_tsquery('english',%s))"},
                                             where=["idxfti @@ plainto_tsquery('english',%s)"], params=[searchterm],
                                             select_params=[searchterm, searchterm]).order_by('-rank')
        paginator = Paginator(results_list, 10)
        try:
            results = paginator.page(page)
        except(EmptyPage, InvalidPage):
            results = paginator.page(paginator.num_pages)
        for result in results:
            result.snippet = smart_truncate(result.searchtext, searchterm)
        return render(request, 'search.html', {'results': results, 'searchterm': searchterm})


def smart_truncate(content, searchterm, surrounding_words=15, suffix='...'):
    words = content.split(' ')
    searchterm = remove_punctuation_to_lower(searchterm)
    trimmed_words = map(remove_punctuation_to_lower, words)
    if remove_punctuation_to_lower(searchterm) in trimmed_words:
        index = trimmed_words.index(searchterm.lower())
        startindex = index - surrounding_words
        endindex = index + surrounding_words
        if startindex < 0:
            startindex = 0
            endindex = 2 * surrounding_words
        if endindex >= len(words):
            endindex = len(words) - 1
            startindex = endindex - (2 * surrounding_words)
            if startindex < 0:
                startindex = 0
        result = ' '.join(words[startindex:endindex])
        if startindex > 0:
            result = suffix + ' ' + result
        if endindex < len(words) - 1:
            result = result + ' ' + suffix
        return result
    else:
        return ' '.join(words[0:2 * surrounding_words])


def remove_punctuation_to_lower(text):
    pattern = re.compile('([^\s\w]|_)+')
    return pattern.sub('', text).lower()


@csrf_exempt
def locator(request):
    if request.method != 'POST':
        raise Http404

    if 'lat' not in request.POST or 'long' not in request.POST or 'acc' not in request.POST or 'time' not in request.POST:
        raise Http404

    location = Location()
    location.latitude = request.POST.get('lat')
    location.longitude = request.POST.get('long')
    location.accuracy = request.POST.get('acc')
    location.devicetimestamp = datetime.datetime.fromtimestamp(Decimal(request.POST.get('time')) / 1000)

    location.save()

    return HttpResponse('')