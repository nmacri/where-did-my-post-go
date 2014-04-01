import pytumblr
from datetime import date, datetime,timedelta
import pandas as pd
import pandas.io.sql as psql
from collections import Counter
import networkx as nx
import numpy as np
import json

import app


class flirt_and_reciprocate_bot(object):
    
    def __init__(self):


        secrets_file = open('secrets.json','rb')
        secrets = json.load(secrets_file)
        secrets_file.close()

        self.blog_name = "wheredidmypostgo"

        # Build an Authorized Tumblr Client
        self.tb_client = pytumblr.TumblrRestClient(**secrets['tumblr_tokens'])
        self.etl_controller = app.etl_controller()

        max_end_date = date.today() - timedelta(days=3)


        sql = """
        select blog_name, avg(ClosenessCentrality) as 'ClosenessCentrality'
        from tb_reblog_graphs
        where reblogged_root_name in (%s)
        and end_date > '%s'
        and blog_name not in ('wheredidmypostgo', %s)
        group by blog_name
        order by avg(ClosenessCentrality) DESC
        """ % (",".join(self.etl_controller.target_blogs), max_end_date.isoformat() , ",".join(self.etl_controller.target_blogs))
        
        self.influencer_df = psql.read_frame(sql,self.etl_controller.mysql_connection)
        self.influencer_df['pdf'] = self.influencer_df.ClosenessCentrality / self.influencer_df.ClosenessCentrality.sum()
        self.influencer_df['cdf'] = self.influencer_df.sort(column='pdf',ascending=False).pdf.cumsum()
        
        sql = """
        select tag
        from tb_posts
        inner join tb_posttag_level on tb_posttag_level.`post_id` = tb_posts.id
        where tb_posts.blog_name = 'wheredidmypostgo'
        """
        curs = self.etl_controller.mysql_connection.cursor()
        curs.execute(sql)
        all_tags = curs.fetchall()
            
        self.most_common_tags = [t[0] for t in Counter(all_tags).most_common(n=200)]
        
        curs.close()
        
        response = self.tb_client.posts('wheredidmypostgo', notes_info='true')
        self.posts = response['posts']
        for offset in range(20,response['total_posts'],20):
            response = self.tb_client.posts('wheredidmypostgo', notes_info='true', offset=offset)
            self.posts.extend(response['posts'])
            
        self.notes = []
        
        for p in self.posts:
            if p['note_count'] > 0:
                self.notes.extend(p['notes'])
                
        self.notes_df = pd.DataFrame(self.notes)
        self.notes_df['date'] = self.notes_df.timestamp.apply(float).apply(datetime.fromtimestamp)
        
        self.todays_notes = self.notes_df[self.notes_df.date >= (datetime.now() - timedelta(hours=4))].sort(column='date', ascending=False).head(50)
        
    def draw_hub_influencer(self):
        return self.influencer_df[self.influencer_df.cdf > pd.np.random.random()].head(1).blog_name.values[0]

    
    def reciprocate(self):
        # Follow Everyone Back
        for user in self.tb_client.followers('wheredidmypostgo')['users']:
            if user['following'] == False:
                self.tb_client.follow(user['url'])
        
        # Like for Like
        for i,blog_name in self.todays_notes[self.todays_notes.type == 'like'].blog_name.iteritems():
            try:
                blog_info = self.tb_client.blog_info(blog_name)['blog']
                total_posts = blog_info['posts']
                
                offset = int(pd.np.random.rand()* (total_posts-20))
                posts = self.tb_client.posts(blog_name, offset=offset, reblog_info='true')['posts']
                original_posts = [p for p in posts if 'reblogged_from_name' not in p.keys()]
                top_post = sorted(original_posts,key=lambda p: p['note_count'],reverse=True)[0]
                self.tb_client.like(top_post['id'],top_post['reblog_key'])
                print "liked ", top_post['short_url']
            except Exception, e:
                print (e)
                
        # Follow for Reblog
        for i,blog_url in self.todays_notes[self.todays_notes.type == 'reblog'].blog_url.iteritems():
            try:
                print "following", blog_url
                self.tb_client.follow(blog_url)
            except Exception, e:
                print (e)
        
    def flirt_with_hub(self):
        
        ## Hubs
        hub = self.draw_hub_influencer()
        print "flirting with hub ", hub
        
        # Pull 10 Posts
        targets = []
        attempts = 0
        while len(targets) < 10 and attempts <10:
            try:
                blog_info = self.tb_client.blog_info(hub)['blog']
                total_posts = blog_info['posts']
                offset = int(pd.np.random.rand()* (total_posts-20))
                posts = self.tb_client.posts(hub, offset=offset, reblog_info='true')['posts']
                top_post = sorted(posts,key=lambda p: p['note_count'],reverse=True)[0]
                targets.append(top_post)
                attempts += 1
            except Exception, e:
                attempts += 1
                
        # Follow the hub
        if not blog_info['followed']:
            self.tb_client.follow(blog_info['url'])
            print "following ", blog_info['url']
        
        # Reblog one relevent post if it exists and like 3 other targets
        def relevence(post):
            tag_score = set(self.most_common_tags + self.etl_controller.target_tags).intersection(set(post['tags']))
            caption_score = set(self.most_common_tags + self.etl_controller.target_tags).intersection(set(post['slug'].split('-')))
            return len(caption_score) + len(tag_score)
        
        if len(targets) > 0:
            relevent_posts = sorted([post for post in targets if relevence(post) > 0], key=lambda post: relevence(post), reverse = True)
                                      
            for target in relevent_posts:
                self.tb_client.like(target['id'],target['reblog_key'])
                print "liked ", target['short_url']
            return True
        else:
            print "no suitable post targets found"
            return False


    def crawl_target_tags(self):

        tags = self.etl_controller.target_tags
        pd.np.random.shuffle(tags)

        follows = 0

        for tag in tags:

            posts = self.tb_client.tagged(tag)

            for post in posts:

                if post['note_count'] > 20:

                    hydrated_root_post = self.tb_client.posts(post['blog_name'],id=post['id'],notes_info='true',reblog_info='true')
                    
                    reblog_tree = []
                    
                    for note in hydrated_root_post['posts'][0]['notes']:
                        if note['type'] == 'reblog':
                            reblog_tree.append(self.tb_client.posts(note['blog_name'],id=note['post_id'],reblog_info='true'))
                            
                    additional_posts = [0]
                    post_missing = False

                    while len(additional_posts)>0 and not post_missing:
                        
                        reblogged_from = set((p['posts'][0]['reblogged_from_name'],p['posts'][0]['reblogged_from_id'])
                                                for p in reblog_tree if 'reblogged_from_name' in p['posts'][0].keys())
                    
                        additional_posts = [r for r in reblogged_from if unicode(r[1]) not in [unicode(p['posts'][0]['id']) for p in reblog_tree]]
                        
                        for a in additional_posts:
                            additional_post = self.tb_client.posts(a[0],id=a[1],reblog_info='true')
                            if 'posts' in additional_post.keys():
                                reblog_tree.append(additional_post)
                            else:
                                post_missing = True
                            
                    reblog_edges = [{'reblog': (p['posts'][0]['blog_name'],p['posts'][0]['id']),
                                         'reblogged_from': (p['posts'][0]['reblogged_from_name'],p['posts'][0]['reblogged_from_id'])} 
                                        for p in reblog_tree if 'reblogged_from_name' in p['posts'][0].keys()]
                    
                    G = nx.DiGraph()

                    for edge in reblog_edges:
                        G.add_edge(edge['reblogged_from'][0],edge['reblog'][0])
                    
                    centrality = nx.closeness_centrality(G) 

                    for hub in sorted(centrality, key=lambda k: centrality[k], reverse=True)[0:5]:
                        print "flirting with hub", hub

                        # Pull 3 Posts
                        targets = []
                        attempts = 0
                        while len(targets) < 9 and attempts <10:
                            try:
                                blog_info = self.tb_client.blog_info(hub)['blog']
                                total_posts = blog_info['posts']
                                offset = int(pd.np.random.rand()* (total_posts-20))
                                posts = self.tb_client.posts(hub, offset=offset, reblog_info='true')['posts']
                                top_post = sorted(posts,key=lambda p: p['note_count'],reverse=True)[0]
                                targets.append(top_post)
                                attempts += 1
                            except Exception, e:
                                attempts += 1
                                
                        # Follow the hub if not already following
                        if not blog_info['followed'] and follows < 15:
                            self.tb_client.follow(blog_info['url'])
                            print "following ", blog_info['url']
                            follows += 1
                        
                        # like 2 most relevent target posts
                        def relevence(post):
                            tag_score = set(self.most_common_tags + self.etl_controller.target_tags).intersection(set(post['tags']))
                            caption_score = set(self.most_common_tags + self.etl_controller.target_tags).intersection(set(post['slug'].split('-')))
                            return len(caption_score) + len(tag_score)
                        
                        if len(targets) > 0:
                            relevent_posts = sorted([post for post in targets if relevence(post) > 0], key=lambda post: relevence(post), reverse = True)
                                                      
                            for target in relevent_posts[0:1]:
                                self.tb_client.like(target['id'],target['reblog_key'])
                                print "liked ", target['short_url']
                        else:
                            print "no suitable post targets found"

                    else:
                        pass


if __name__ == '__main__':

    bot = flirt_and_reciprocate_bot()

    success_count = 0
    while success_count < 10:
        success = bot.flirt_with_hub()
        if success:
            success_count += 1
        else:
            continue 

    bot.crawl_target_tags()

    bot.reciprocate()

    