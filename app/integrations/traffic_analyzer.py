class TrafficAnalyzer:
    def __init__(self, ga4, gads, yt, meta):
        self.ga4 = ga4
        self.gads = gads
        self.yt = yt
        self.meta = meta

    def score(self, page_path: str, keyword: str):
        score = 0

        # GA4 → traffic indicator
        pageviews = self.ga4.get_pageviews(page_path)
        if pageviews < 20:
            score += 40
        elif pageviews < 100:
            score += 20

        # Ads → klikgedrag
        ads = self.gads.get_keyword_metrics(keyword)
        if ads:
            ctr = ads[0]["ctr"]
            if ctr < 0.02:
                score += 25
            else:
                score += 10

        # YouTube → content trend
        yt = self.yt.search(keyword)
        if yt:
            score += 15

        # Meta Ads
        meta = self.meta.get_campaign_metrics()
        if meta:
            score += 10

        return min(score, 100)
