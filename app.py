import json
import os
import urllib, cStringIO
from collections import Counter

from PIL import Image as Im
import mysql.connector
import pytumblr
import networkx as nx
import pandas as pd
import colorific
from matplotlib import colors

from images2gif import writeGif
from PIL import Image
import random


class etl_controller(object):
    """ETL methods for collecting and storing reblog graphs"""
    def __init__(self):
        # Auth credentials are stored in secrets.json
        secrets_file = open('secrets.json','rb')
        secrets = json.load(secrets_file)
        secrets_file.close()

        # Build an Authorized Tumblr Client
        self.tumblr_client = pytumblr.TumblrRestClient(**secrets['tumblr_tokens'])

        # Build an Authorized Database Connection
        self.mysql_connection = mysql.connector.connect(**secrets['mysql'])


class gif_generator(object):
    """GIF graph generation methods"""
    def __init__(self):

        # Auth credentials are stored in secrets.json
        secrets_file = open('secrets.json','rb')
        secrets = json.load(secrets_file)
        secrets_file.close()

        # Build an Authorized Tumblr Client
        self.tumblr_client = pytumblr.TumblrRestClient(**secrets['tumblr_tokens'])

        # Build an Authorized Database Connection
        self.mysql_connection = mysql.connector.connect(**secrets['mysql'])

    def extract_reblog_graph(self, post_url):

        print "Building graph . . ."
        G = nx.DiGraph()

        sql = """
        select blog_name, date
        from tb_posts
        where post_url = %s
        order by date ASC
        """
        curs = self.mysql_connection.cursor()
        curs.execute(sql,(post_url,))
        for node in curs:
            G.add_node(node[0])
            self.blog_name = node[0]
            self.post_date = node[1]
        curs.close()

        sql = """
        select reblogged_from_name, blog_name, date
        from tb_posts
        where reblogged_root_url = %s
        order by date ASC
        """

        curs = self.mysql_connection.cursor()
        curs.execute(sql,(post_url,))
        for edge in curs:
            G.add_edge(edge[0],edge[1])
            G.edge[edge[0]][edge[1]]['date'] = edge[2]
        curs.close()

        connected=nx.connected_component_subgraphs(G.to_undirected())[0]
        self.G = G.subgraph(connected.nodes())

        for edge in self.G.edges_iter(data=True):
            edge[2]['timestamp'] = int(edge[2]['date'].strftime('%s'))
        
        print "Graph Built. Sequencing edges . . ."
        print "    node count = ", str(self.G.number_of_nodes())

        if self.G.number_of_nodes() < 80:
            frames = int(self.G.number_of_nodes() / 1.7)
        elif self.G.number_of_nodes() < 200:
            frames = 45
        elif self.G.number_of_nodes() < 1000:
            frames = 36
        elif self.G.number_of_nodes() < 2000:
            frames = 30
        else:
            frames = 24

        print "    frame count = ", str(frames)

            
        timestamps = [int(data['date'].strftime('%s')) for fr,to,data in self.G.edges_iter(data=True)]

        # Cardinal Sequencing
        step = max(len(timestamps)/frames,1)

        self.edge_sequence = [sorted(self.G.edges(data=True), key=lambda e:e[2]['timestamp'])[0:x] for x in xrange(step,len(timestamps),step)]
        self.edge_sequence_dates = [max([d['date'] for f,t,d in edges]) for edges in self.edge_sequence]

        print "Edges Sequenced. Classifying Nodes by Centrality . . . "
        # Ordinal Sequencing Method
        #step = (max(timestamps) - min(timestamps))/frames
        #edge_sequence = [[(fr,to) for fr,to,data in G.edges_iter(data=True) if data['timestamp'] <= x+step] for x in xrange(min(timestamps),max(timestamps),step)]

        centrality = nx.closeness_centrality(self.G,normalized=True)
        centrality_class = pd.Series(centrality)

        threshold = 0.0001
        while threshold <= 1:
            try:
                centrality_class[centrality_class<threshold] = 1
                cat = pd.qcut(centrality_class[centrality_class!=1],
                              5,labels=[2,3,4,5,6])
                centrality_class[centrality_class!=1] = pd.np.array(cat)
                break
            except Exception, e:
                threshold += 0.0001
                continue


        self.centrality_class = centrality_class.to_dict()
        print "Nodes calssified."


    def pick_colors(self):
    
        response = self.tumblr_client.posts(self.blog_name, offset = random.randint(0,150))
        thumbnails = [post['photos'][0]['alt_sizes'][-1] for post in response['posts'] if 'photos' in post.keys()]

        blog_page = urllib.urlopen(response['blog']['url'])
        background_colors = ["#"+line.strip().split("#")[1][0:6] for line in blog_page.readlines() if 'background: ' in line and "#" in line]
        background_colors = [color.lower() for color in background_colors if color.startswith('#') and len(color) == 7 and ' ' not in color]

        if len(background_colors) == 0:
            background_colors = ['#ffffff']

        most_common_background_color = Counter(background_colors).most_common(1)[0][0]
        most_common_background_color

        x=0
        y=0

        height = sum([t['height'] for t in thumbnails]) / (len(thumbnails) / 3)
        width = sum([t['width'] for t in thumbnails]) / (len(thumbnails) / 4)

        grid_image = Im.new("RGB", (width, height))

        for i,thumbnail in enumerate(thumbnails):

            thumbnail_file = cStringIO.StringIO(urllib.urlopen(thumbnail['url']).read())
            thumbnail_image = Im.open(thumbnail_file)
            
            grid_image.paste(thumbnail_image, (x,y))
            grid_image.save('grid.jpg')
            
            if (i+1) % 5 == 0:
                x = 0
                y += thumbnail['height']
            else:
                x += thumbnail['width']
                
        photo_pallete = colorific.extract_colors(Im.open(open('grid.jpg','rb')), 
                                                 min_saturation=0.15,
                                                 max_colors=7)
        colorific.save_palette_as_image('photo.png',photo_pallete)

        color_count = len(background_colors)
        color_counter = Counter(background_colors)

        try:
            page_pallete = colorific.Palette([colorific.Color(colorific.hex_to_rgb(color), 
                       prominence = float(count)/color_count) 
                       for color,count in color_counter.items()],None)
        except:
            page_pallete = colorific.Palette(colors=[colorific.Color(value=(255, 255, 255), prominence=1.0)], bgcolor=None)

        colorific.save_palette_as_image('page.png',page_pallete)


        self.sorted_photo_pallete = sorted(photo_pallete.colors, key=lambda c:colorific.colorsys.rgb_to_hsv(*colorific.norm_color(c.value))[1], reverse=True)
        self.sorted_page_pallete = sorted(page_pallete.colors, key=lambda c:colorific.colorsys.rgb_to_hsv(*colorific.norm_color(c.value))[1], reverse=False)

        from matplotlib import colors

        bg_i = random.randint(0,len(self.sorted_page_pallete)-1)
        self.background_color = colorific.norm_color(self.sorted_page_pallete[bg_i].value)

        # make a color map of fixed colors
        self.node_cmap = colors.ListedColormap([self.background_color,
                                      colorific.norm_color(self.sorted_photo_pallete[5].value),
                                      colorific.norm_color(self.sorted_photo_pallete[4].value),
                                      colorific.norm_color(self.sorted_photo_pallete[3].value),
                                      colorific.norm_color(self.sorted_photo_pallete[2].value),
                                      colorific.norm_color(self.sorted_photo_pallete[1].value),
                                      colorific.norm_color(self.sorted_photo_pallete[0].value)])
        bounds=[0,1,2,3,4,5,6]
        norm = colors.BoundaryNorm(bounds, self.node_cmap.N, clip=True)


        self.edge_cmap = colors.ListedColormap([self.background_color,
                                      colorific.norm_color(self.sorted_photo_pallete[6].value)])
        bounds=[0,1]
        norm = colors.BoundaryNorm(bounds, self.edge_cmap.N, clip=True)


    def draw_graph_frames(self):

        # use graphviz to find layout
        if self.G.number_of_nodes() > 2000:
            layout = "sfdp"
        elif self.G.number_of_nodes() > 400:
            r = random.random()
            if r < .40:
                layout = "dot"
            elif r < .70:
                layout="twopi"
            else:
                layout="fdp"
        elif self.G.number_of_nodes() > 150:
            r = random.random()
            if r < .50:
                layout = "dot"
            elif r < .75:
                layout="twopi"
            elif r < .90:
                layout = "fdp"
        else:
            r = random.random()
            if r < .60:
                layout = "twopi"
            else:
                layout="fdp"

        pos=nx.graphviz_layout(self.G,prog=layout)

        print "Using layout ", layout

        if random.random() > 0.5 and layout != "sfdp" and layout != "fdp":
            new_layout_for_each_frame = True
            print "Using new layout for each frame"
        else:
            new_layout_for_each_frame = False
            print "Using one layout for entire GIF"

        for i,edge_list in enumerate(self.edge_sequence):

            subgraph = nx.DiGraph(edge_list)
            
            if new_layout_for_each_frame:
                
                graph_to_draw = subgraph
                pos=nx.graphviz_layout(graph_to_draw,prog=layout)

                centrality = nx.closeness_centrality(graph_to_draw,normalized=True)
                centrality_class = pd.Series(centrality)
                threshold = 0.0001
                while threshold <= 1:
                    try:
                        centrality_class[centrality_class<threshold] = 1
                        cat = pd.qcut(centrality_class[centrality_class!=1],
                                      5,labels=[2,3,4,5,6])
                        centrality_class[centrality_class!=1] = pd.np.array(cat)
                        break
                    except Exception, e:
                        threshold += 0.0001
                        continue
                c_class = centrality_class.to_dict()
                node_colors = [c_class[n] for n in graph_to_draw]
                edge_colors = [colorific.norm_color(self.sorted_photo_pallete[6].value) for edge in graph_to_draw.edges(data=False)]
                self.node_cmap = colors.ListedColormap([colorific.norm_color(self.sorted_photo_pallete[5].value),
                                      colorific.norm_color(self.sorted_photo_pallete[4].value),
                                      colorific.norm_color(self.sorted_photo_pallete[3].value),
                                      colorific.norm_color(self.sorted_photo_pallete[2].value),
                                      colorific.norm_color(self.sorted_photo_pallete[1].value),
                                      colorific.norm_color(self.sorted_photo_pallete[0].value)])
            else:

                graph_to_draw = self.G
                node_colors = [self.centrality_class[n] if n in subgraph.nodes() else 0 for n in graph_to_draw]
                edge_colors = [1 if edge in subgraph.edges() else 0 for edge in graph_to_draw.edges(data=False)]
            
            import matplotlib.pyplot as plt

            fig = plt.figure(1,figsize= (10,min(max([10,self.G.number_of_nodes() / 30]),15)))

            axes = fig.add_subplot(111)

            # cf = axes.get_figure()
            # cf.set_facecolor('w')

            # plt.hold(True)
            
            #gvcolor, wc, ccomps, tred, sccmap, fdp, circo, neato, acyclic, nop, gvpr, dot, sfdp.
            # draw nodes, coloring by rtt ping time
            nx.draw(graph_to_draw,pos=pos,ax=axes,hold=True,
                    edge_color=edge_colors,
                    node_color=node_colors,
                    cmap=self.node_cmap,
                    edge_cmap=None if new_layout_for_each_frame else self.edge_cmap,
                    with_labels=False,
                    alpha=.3 if layout == 'sfdp' else 1,
                    arrows=False,
                    node_shape='.', #'.' if layout == 'sfdp ' else 'o',
                    node_size=50000/graph_to_draw.number_of_nodes(),
                    font_size=24,
                    linewidths=0)

            # node_collection = nx.draw_networkx_nodes(graph_to_draw,pos=pos,ax=axes,
            #         node_color=node_colors,
            #         cmap=self.node_cmap,
            #         alpha=.3 if layout == 'sfdp' else 1,
            #         node_shape='.', #'.' if layout == 'sfdp ' else 'o',
            #         node_size=50000/graph_to_draw.number_of_nodes(),
            #         edgesize=0)

            # edge_collection = nx.draw_networkx_edges(graph_to_draw,pos=pos,ax=axes,
            #         edge_color=edge_colors,
            #         edge_cmap=None if new_layout_for_each_frame else self.edge_cmap,
            #         alpha=.3 if layout == 'sfdp' else 1,
            #         arrows=False)

            # plt.draw_if_interactive()


            # adjust the plot limits
            xmax=1.02*max(xx for xx,yy in pos.values())
            ymax=1.02*max(yy for xx,yy in pos.values())
            plt.xlim(0,xmax)
            plt.ylim(0,ymax)
            
            #add text
            axes.text(0,0,
                      self.edge_sequence_dates[i].strftime('%Y-%m-%d %H:%M'),
                      fontsize=14,
                      color=colorific.norm_color(self.sorted_photo_pallete[6].value))
                        
            fig.savefig('frame'+str(i)+'.png', dpi=400/min(max([10,self.G.number_of_nodes() / 30]),15), facecolor = self.background_color)
            plt.clf()
            plt.close()
    
    def write_frames_to_gif(self):    
        key = "%x" % random.getrandbits(32)
        writeGif('animated'+key+'.gif',
                 [Image.open('frame'+str(i)+'.png').convert(mode="RGB",palette=Image.ADAPTIVE) for i in range(len(self.edge_sequence))],
                 dither=True)
        print "saving as animated"+key+".gif"
        print "\n"