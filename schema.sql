# ************************************************************
# Sequel Pro SQL dump
# Version 4004
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.6.15)
# Database: wdmpg
# Generation Time: 2014-03-31 00:47:19 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table tb_blogs
# ------------------------------------------------------------

DROP TABLE IF EXISTS `tb_blogs`;

CREATE TABLE `tb_blogs` (
  `name` varchar(255) NOT NULL DEFAULT '',
  `posts_inspected` tinyint(1) DEFAULT NULL,
  `posts_last_inspected` datetime DEFAULT NULL,
  `info_inspected` tinyint(1) DEFAULT NULL,
  `info_last_inspected` datetime DEFAULT NULL,
  `ask` tinyint(1) DEFAULT NULL,
  `ask_anon` tinyint(1) DEFAULT NULL,
  `can_send_fan_mail` tinyint(1) DEFAULT NULL,
  `facebook` varchar(11) DEFAULT NULL,
  `facebook_opengraph_enabled` tinyint(1) DEFAULT NULL,
  `tweet` varchar(11) DEFAULT NULL,
  `twitter_enabled` tinyint(1) DEFAULT NULL,
  `twitter_send` tinyint(1) DEFAULT NULL,
  `updated` datetime DEFAULT NULL,
  `description` text,
  `title` varchar(255) DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  `share_likes` tinyint(1) DEFAULT NULL,
  `posts` int(11) DEFAULT NULL,
  `is_nsfw` tinyint(1) DEFAULT NULL,
  `likes` int(11) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table tb_notes
# ------------------------------------------------------------

DROP TABLE IF EXISTS `tb_notes`;

CREATE TABLE `tb_notes` (
  `id` binary(16) NOT NULL DEFAULT '\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0',
  `blog_name` varchar(255) NOT NULL DEFAULT '',
  `blog_url` varchar(255) DEFAULT NULL,
  `target_post_id` bigint(35) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `type` enum('LIKE','REBLOG') DEFAULT NULL,
  `post_id` bigint(35) DEFAULT NULL,
  `added_text` text,
  PRIMARY KEY (`id`),
  KEY `blog_name` (`blog_name`),
  KEY `target_post_id` (`target_post_id`),
  KEY `post_id` (`post_id`),
  KEY `type` (`type`),
  KEY `timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table tb_posts
# ------------------------------------------------------------

DROP TABLE IF EXISTS `tb_posts`;

CREATE TABLE `tb_posts` (
  `id` bigint(35) NOT NULL,
  `blog_name` varchar(255) DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `featured_in_tag` varchar(255) DEFAULT NULL,
  `liked` tinyint(1) DEFAULT NULL,
  `followed` tinyint(1) DEFAULT NULL,
  `note_count` bigint(20) DEFAULT NULL,
  `post_url` varchar(255) DEFAULT NULL,
  `reblog_key` varchar(63) DEFAULT NULL,
  `reblogged_from_id` bigint(35) DEFAULT NULL,
  `reblogged_from_name` varchar(255) DEFAULT NULL,
  `reblogged_from_url` varchar(255) DEFAULT NULL,
  `reblogged_from_title` varchar(255) DEFAULT NULL,
  `reblogged_root_title` varchar(255) DEFAULT NULL,
  `reblogged_root_name` varchar(255) DEFAULT NULL,
  `reblogged_root_url` varchar(255) DEFAULT NULL,
  `source` varchar(255) DEFAULT NULL,
  `short_url` varchar(63) DEFAULT NULL,
  `type` enum('ANSWER','AUDIO','CHAT','LINK','PHOTO','QUOTE','TEXT','VIDEO') DEFAULT NULL,
  `notes_last_inspected` datetime DEFAULT NULL,
  `notes_per_day` float DEFAULT NULL,
  `reblogs_last_crawled` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `blog_name` (`blog_name`),
  KEY `reblogged_root_url` (`reblogged_root_url`),
  KEY `reblogged_from_name` (`reblogged_from_name`),
  KEY `reblogged_from_id` (`reblogged_from_id`),
  KEY `date` (`date`),
  KEY `notes_last_inspected` (`notes_last_inspected`),
  KEY `notes_per_day` (`notes_per_day`),
  KEY `reblogged_root_name` (`reblogged_root_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table tb_posttag_level
# ------------------------------------------------------------

DROP TABLE IF EXISTS `tb_posttag_level`;

CREATE TABLE `tb_posttag_level` (
  `id` binary(16) NOT NULL DEFAULT '\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0',
  `post_id` bigint(35) DEFAULT NULL,
  `tag` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table tb_reblog_graphs
# ------------------------------------------------------------

DROP TABLE IF EXISTS `tb_reblog_graphs`;

CREATE TABLE `tb_reblog_graphs` (
  `start_date` date NOT NULL DEFAULT '0000-00-00',
  `end_date` date NOT NULL DEFAULT '0000-00-00',
  `reblogged_root_name` varchar(255) NOT NULL DEFAULT '0',
  `blog_name` varchar(255) NOT NULL DEFAULT '',
  `lookback_days` int(11) DEFAULT NULL,
  `ClosenessCentrality` float DEFAULT NULL COMMENT 'ClosenessCentrality at a node is 1/average distance to all other nodes.  The distance used in the shortest path \n			calculations for each edge is 1 / reblog_count. The implicit assumption is that nodes that have a short distance to other nodes can disseminate\n			information more quickly on the network. See\n			Freeman, L.C., 1979. Centrality in networks: I. conceptual clarifcation. Social Networks 1, 215-239.\n			Borgatti, Stephen P., and Martin G. Everett. "A graph-theoretic perspective on centrality." Social networks 28, no. 4 (2006): 466-484.',
  `SuccessiveReblogs` int(11) DEFAULT NULL COMMENT 'SuccessiveReblogs is the count of reblogs in the full BFS tree from a given node',
  `DirectReblogs` int(11) DEFAULT NULL COMMENT 'DirectReblogs is the count of direct child reblogs from a given node',
  PRIMARY KEY (`reblogged_root_name`,`blog_name`,`start_date`,`end_date`),
  KEY `start_date` (`start_date`),
  KEY `reblogged_root_name` (`reblogged_root_name`),
  KEY `end_date` (`end_date`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='The Reblog Graph\nA directed graph (networkx.DiGraph) of rebloogs from a particular root blog\nnodes represent blogs, edges represent reblogged_from > reblogged_to relationships, \nedge weights represent counts of reblogs along a directed edge\n\nThe Metrics\nClosenessCentrality at a node is 1/average distance to all other nodes.  The distance used in the shortest path \n	calculations for each edge is 1 / reblog_count. The implicit assumption is that nodes that have a short distance to other nodes can disseminate\n	information more quickly on the network. See\n	Freeman, L.C., 1979. Centrality in networks: I. conceptual clarifcation. Social Networks 1, 215-239.\n	Borgatti, Stephen P., and Martin G. Everett. "A graph-theoretic perspective on centrality." Social networks 28, no. 4 (2006): 466-484.\n\nDirectReblogs the count of direct child reblogs from a given node\n\nSuccessiveReblogs the count of reblogs in the full BFS tree from a given node';



# Dump of table wdmpg_submissions
# ------------------------------------------------------------

DROP TABLE IF EXISTS `wdmpg_submissions`;

CREATE TABLE `wdmpg_submissions` (
  `id` bigint(36) unsigned NOT NULL,
  `date` datetime DEFAULT NULL,
  `type` varchar(31) DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `description` text,
  `blog_name` varchar(255) DEFAULT NULL,
  `liked` tinyint(1) DEFAULT NULL,
  `followed` tinyint(1) DEFAULT NULL,
  `post_url` varchar(255) DEFAULT NULL,
  `reblog_key` varchar(63) DEFAULT NULL,
  `response_generated` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table wdmpg_targets
# ------------------------------------------------------------

DROP TABLE IF EXISTS `wdmpg_targets`;

CREATE TABLE `wdmpg_targets` (
  `type` enum('BLOG','POST','TAG') NOT NULL DEFAULT 'BLOG',
  `blog_name` varchar(255) NOT NULL DEFAULT '',
  `value` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`type`,`blog_name`,`value`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
