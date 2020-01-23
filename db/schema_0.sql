-- MySQL dump 10.13  Distrib 5.1.73, for redhat-linux-gnu (x86_64)
--
-- Host: localhost    Database: iris
-- ------------------------------------------------------
-- Server version	5.1.73

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `application`
--

CREATE SCHEMA IF NOT EXISTS `iris` DEFAULT CHARACTER SET utf8;
USE `iris`;

DROP TABLE IF EXISTS `application`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `application` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `key` varchar(64) NOT NULL,
  `context_template` text,
  `summary_template` text,
  `sample_context` text,
  `mobile_template` text,
  `auth_only` tinyint(1) DEFAULT '0',
  `allow_other_app_incidents` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `allow_authenticating_users` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `secondary_key` varchar(64),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_idx` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `incident`
--

DROP TABLE IF EXISTS `incident`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `incident` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `plan_id` bigint(20) NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime DEFAULT NULL,
  `context` text,
  `owner_id` bigint(20) DEFAULT NULL,
  `application_id` int(11) NOT NULL,
  `current_step` int(11) NOT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_incident_plan_id` (`plan_id`),
  KEY `ix_incident_updated` (`updated`),
  KEY `ix_incident_owner_id` (`owner_id`),
  KEY `ix_incident_active` (`active`),
  KEY `ix_incident_application_id` (`application_id`),
  KEY `ix_incident_created` (`created`),
  CONSTRAINT `incident_ibfk_1` FOREIGN KEY (`plan_id`) REFERENCES `plan` (`id`),
  CONSTRAINT `incident_ibfk_2` FOREIGN KEY (`owner_id`) REFERENCES `user` (`target_id`),
  CONSTRAINT `incident_ibfk_3` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `message`
--

DROP TABLE IF EXISTS `message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `message` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `batch` varchar(32) DEFAULT NULL,
  `created` datetime NOT NULL,
  `sent` datetime DEFAULT NULL,
  `application_id` int(11) NOT NULL,
  `target_id` bigint(20) NOT NULL,
  `destination` varchar(255) DEFAULT NULL,
  `mode_id` int(11) DEFAULT NULL,
  `plan_id` bigint(20) DEFAULT NULL,
  `priority_id` int(11) NOT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `body` text,
  `incident_id` bigint(20) DEFAULT NULL,
  `plan_notification_id` bigint(20) DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  `template_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `plan_id` (`plan_id`),
  KEY `ix_message_sent` (`sent`),
  KEY `ix_message_created` (`created`),
  KEY `ix_message_incident_id` (`incident_id`),
  KEY `ix_message_plan_notification_id` (`plan_notification_id`),
  KEY `ix_message_priority_id` (`priority_id`),
  KEY `ix_message_batch` (`batch`),
  KEY `ix_message_application_id` (`application_id`),
  KEY `ix_message_target_id` (`target_id`),
  KEY `ix_message_mode_id` (`mode_id`),
  KEY `ix_message_active` (`active`),
  KEY `message_ibfk_8` (`template_id`),
  CONSTRAINT `message_ibfk_1` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`),
  CONSTRAINT `message_ibfk_2` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`),
  CONSTRAINT `message_ibfk_3` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`),
  CONSTRAINT `message_ibfk_4` FOREIGN KEY (`plan_id`) REFERENCES `plan` (`id`),
  CONSTRAINT `message_ibfk_5` FOREIGN KEY (`priority_id`) REFERENCES `priority` (`id`),
  CONSTRAINT `message_ibfk_6` FOREIGN KEY (`incident_id`) REFERENCES `incident` (`id`),
  CONSTRAINT `message_ibfk_7` FOREIGN KEY (`plan_notification_id`) REFERENCES `plan_notification` (`id`),
  CONSTRAINT `message_ibfk_8` FOREIGN KEY (`template_id`) REFERENCES `template` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

DROP TABLE IF EXISTS `message_changelog`;
CREATE TABLE `message_changelog` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `message_id` bigint(20) NOT NULL,
  `change_type` varchar(255) NOT NULL,
  `old` varchar(255) NOT NULL,
  `new` varchar(255) NOT NULL,
  `description` varchar(255),
  PRIMARY KEY (`id`),
  KEY `ix_message_changelog_message_id` (`message_id`),
  KEY `ix_message_changelog_date` (`date`),
  CONSTRAINT `message_changelog_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

--
-- Table structure for table `mode`
--

DROP TABLE IF EXISTS `mode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mode` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_idx` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `plan`
--

DROP TABLE IF EXISTS `plan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `plan` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `team_id` bigint(20) DEFAULT NULL,
  `description` text,
  `step_count` int(11) NOT NULL,
  `threshold_window` bigint(20) DEFAULT NULL,
  `threshold_count` bigint(20) DEFAULT NULL,
  `aggregation_window` bigint(20) DEFAULT NULL,
  `aggregation_reset` bigint(20) DEFAULT NULL,
  `tracking_key` varchar(255) DEFAULT NULL,
  `tracking_type` varchar(255) DEFAULT NULL,
  `tracking_template` text,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `team_id` (`team_id`),
  KEY `ix_plan_created` (`created`),
  CONSTRAINT `plan_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`target_id`),
  CONSTRAINT `plan_ibfk_2` FOREIGN KEY (`team_id`) REFERENCES `team` (`target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `plan_active`
--

DROP TABLE IF EXISTS `plan_active`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `plan_active` (
  `name` varchar(255) NOT NULL,
  `plan_id` bigint(20) NOT NULL,
  PRIMARY KEY (`name`),
  UNIQUE KEY `plan_id` (`plan_id`),
  CONSTRAINT `plan_active_ibfk_1` FOREIGN KEY (`plan_id`) REFERENCES `plan` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `plan_notification`
--

DROP TABLE IF EXISTS `plan_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `plan_notification` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `plan_id` bigint(20) NOT NULL,
  `step` int(11) NOT NULL,
  `template` varchar(255) DEFAULT NULL,
  `target_id` bigint(20),
  `optional` TINYINT(1) NOT NULL DEFAULT '0',
  `role_id` int(11),
  `priority_id` int(11) NOT NULL,
  `repeat` int(11) NOT NULL DEFAULT '0',
  `wait` int(11) NOT NULL DEFAULT '0',
  `dynamic_index` int(11),
  PRIMARY KEY (`id`),
  KEY `ix_plan_notification_plan_id` (`plan_id`),
  KEY `ix_plan_notification_template` (`template`),
  KEY `ix_plan_notification_role_id` (`role_id`),
  KEY `ix_plan_notification_priority_id` (`priority_id`),
  KEY `ix_plan_notification_target_id` (`target_id`),
  CONSTRAINT `plan_notification_ibfk_1` FOREIGN KEY (`plan_id`) REFERENCES `plan` (`id`),
  CONSTRAINT `plan_notification_ibfk_2` FOREIGN KEY(`template`) REFERENCES `template_active` (`name`) ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT `plan_notification_ibfk_3` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`),
  CONSTRAINT `plan_notification_ibfk_4` FOREIGN KEY (`role_id`) REFERENCES `target_role` (`id`),
  CONSTRAINT `plan_notification_ibfk_5` FOREIGN KEY (`priority_id`) REFERENCES `priority` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dynamic_plan_map`
--

DROP TABLE IF EXISTS `dynamic_plan_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dynamic_plan_map` (
  `incident_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `dynamic_index` int(11) NOT NULL,
  `role_id` int(11) NOT NULL,
  `target_id` bigint(20) NOT NULL,
  PRIMARY KEY (`incident_id`, `dynamic_index`),
  KEY `ix_dynamic_plan_map_incident_id` (`incident_id`),
  CONSTRAINT `dynamic_plan_map_ibfk_1` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`),
  CONSTRAINT `dynamic_plan_map_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `target_role` (`id`),
  CONSTRAINT `dynamic_plan_map_ibfk_3` FOREIGN KEY (`incident_id`) REFERENCES `incident` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `priority`
--

DROP TABLE IF EXISTS `priority`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `priority` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `mode_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_idx` (`name`),
  KEY `ix_priority_mode_id` (`mode_id`),
  CONSTRAINT `priority_ibfk_1` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `response`
--

DROP TABLE IF EXISTS `response`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `response` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created` datetime NOT NULL,
  `message_id` bigint(20) NOT NULL,
  `content` text NOT NULL,
  `source` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_response_message_id` (`message_id`),
  KEY `ix_response_created` (`created`),
  CONSTRAINT `response_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `target`
--

DROP TABLE IF EXISTS `target`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `target` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `type_id` int(11) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_type_idx` (`name`,`type_id`),
  KEY `active_index` (`active`),
  CONSTRAINT `target_ibfk_1` FOREIGN KEY (`type_id`) REFERENCES `target_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `oncall_team`
--

DROP TABLE IF EXISTS `oncall_team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `oncall_team` (
  `target_id` bigint(20) NOT NULL,
  `oncall_team_id` bigint(20) NOT NULL,
  PRIMARY KEY (`target_id`),
  UNIQUE KEY `oncall_team_id_idx` (`oncall_team_id`),
  CONSTRAINT `oncall_team_ibfk_1` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `target_application_mode`
--

DROP TABLE IF EXISTS `target_application_mode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `target_application_mode` (
  `target_id` bigint(20) NOT NULL,
  `application_id` int(11) NOT NULL,
  `priority_id` int(11) NOT NULL,
  `mode_id` int(11) NOT NULL,
  PRIMARY KEY (`target_id`,`application_id`,`priority_id`),
  KEY `application_mode_ibfk_2` (`application_id`),
  KEY `application_mode_ibfk_3` (`priority_id`),
  KEY `application_mode_ibfk_4` (`mode_id`),
  CONSTRAINT `target_application_mode_ibfk_1` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `target_application_mode_ibfk_2` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`),
  CONSTRAINT `target_application_mode_ibfk_3` FOREIGN KEY (`priority_id`) REFERENCES `priority` (`id`),
  CONSTRAINT `target_application_mode_ibfk_4` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `target_default_application_mode`
--

DROP TABLE IF EXISTS `default_application_mode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `default_application_mode` (
  `application_id` int(11) NOT NULL,
  `priority_id` int(11) NOT NULL,
  `mode_id` int(11) NOT NULL,
  PRIMARY KEY (`application_id`,`priority_id`),
  KEY `default_application_mode_ibfk_1` (`application_id`),
  KEY `default_application_mode_ibfk_2` (`priority_id`),
  KEY `default_application_mode_ibfk_3` (`mode_id`),
  CONSTRAINT `default_application_mode_ibfk_1` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`),
  CONSTRAINT `default_application_mode_ibfk_2` FOREIGN KEY (`priority_id`) REFERENCES `priority` (`id`),
  CONSTRAINT `default_application_mode_ibfk_3` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `target_contact`
--

DROP TABLE IF EXISTS `target_contact`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `target_contact` (
  `target_id` bigint(20) NOT NULL,
  `mode_id` int(11) NOT NULL,
  `destination` varchar(255) NOT NULL,
  PRIMARY KEY (`target_id`,`mode_id`),
  KEY `ix_target_contact_mode_id` (`mode_id`),
  CONSTRAINT `target_contact_ibfk_1` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `target_contact_ibfk_2` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `target_mode`
--

DROP TABLE IF EXISTS `target_mode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `target_mode` (
  `target_id` bigint(20) NOT NULL,
  `priority_id` int(11) NOT NULL,
  `mode_id` int(11) NOT NULL,
  PRIMARY KEY (`target_id`,`priority_id`),
  KEY `priority_id` (`priority_id`),
  KEY `ix_target_mode_mode_id` (`mode_id`),
  CONSTRAINT `target_mode_ibfk_1` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `target_mode_ibfk_2` FOREIGN KEY (`priority_id`) REFERENCES `priority` (`id`),
  CONSTRAINT `target_mode_ibfk_3` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `target_reprioritization`
--

DROP TABLE IF EXISTS `target_reprioritization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `target_reprioritization` (
  `target_id` bigint(20) NOT NULL,
  `src_mode_id` int(11) NOT NULL,
  `dst_mode_id` int(11) NOT NULL,
  `count` tinyint(5) unsigned NOT NULL,
  `duration` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`target_id`,`src_mode_id`),
  KEY `target_reprioritization_mode_src_mode_id_fk_idx` (`src_mode_id`),
  KEY `target_reprioritization_mode_dst_mode_id_fk_idx` (`dst_mode_id`),
  CONSTRAINT `target_reprioritization_mode_dst_mode_id_fk` FOREIGN KEY (`dst_mode_id`) REFERENCES `mode` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `target_reprioritization_mode_src_mode_id_fk` FOREIGN KEY (`src_mode_id`) REFERENCES `mode` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `target_reprioritization_target_id_fk` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `target_role`
--
-- Used in plan step, one multiple role can map to same target type
--

DROP TABLE IF EXISTS `target_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `target_role` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `type_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_idx` (`name`),
  KEY `ix_target_role_type_id` (`type_id`),
  CONSTRAINT `target_role_ibfk_1` FOREIGN KEY (`type_id`) REFERENCES `target_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `target_type`
--

DROP TABLE IF EXISTS `target_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `target_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `team`
--

DROP TABLE IF EXISTS `team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `team` (
  `target_id` bigint(20) NOT NULL,
  `manager_id` bigint(20) DEFAULT NULL,
  `director_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`target_id`),
  UNIQUE KEY `target_id` (`target_id`),
  KEY `manager_id` (`manager_id`),
  KEY `director_id` (`director_id`),
  CONSTRAINT `team_ibfk_1` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`),
  CONSTRAINT `team_ibfk_2` FOREIGN KEY (`manager_id`) REFERENCES `user` (`target_id`),
  CONSTRAINT `team_ibfk_3` FOREIGN KEY (`director_id`) REFERENCES `user` (`target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `template`
--

DROP TABLE IF EXISTS `template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `template` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_template_name` (`name`),
  KEY `ix_template_user_id` (`user_id`),
  KEY `ix_template_created` (`created`),
  CONSTRAINT `template_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `template_active`
--

DROP TABLE IF EXISTS `template_active`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `template_active` (
  `name` varchar(255) NOT NULL,
  `template_id` int(11) NOT NULL,
  PRIMARY KEY (`name`),
  UNIQUE KEY `template_id` (`template_id`),
  CONSTRAINT `template_active_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `template` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `template_content`
--

DROP TABLE IF EXISTS `template_content`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `template_content` (
  `template_id` int(11) NOT NULL,
  `application_id` int(11) NOT NULL,
  `mode_id` int(11) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `body` text NOT NULL,
  `call` text,
  `sms` text,
  `im` text,
  `email_subject` varchar(255) DEFAULT NULL,
  `email_text` text,
  `email_html` text,
  PRIMARY KEY (`template_id`,`application_id`,`mode_id`),
  KEY `ix_template_content_template_id` (`template_id`),
  KEY `ix_template_content_application_id` (`application_id`),
  KEY `ix_template_content_mode_id` (`mode_id`),
  CONSTRAINT `template_content_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `template` (`id`),
  CONSTRAINT `template_content_ibfk_2` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`),
  CONSTRAINT `template_content_ibfk_3` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `template_variable`
--

DROP TABLE IF EXISTS `template_variable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `template_variable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `application_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `required` tinyint(1) NOT NULL DEFAULT '0',
  `title_variable` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `ix_template_variable_application_id` (`application_id`),
  CONSTRAINT `template_variable_ibfk_1` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `target_id` bigint(20) NOT NULL,
  `admin` tinyint(1) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`target_id`),
  CONSTRAINT `user_ibfk_1` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_setting`
--

DROP TABLE IF EXISTS `user_setting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_setting` (
  `user_id` bigint(20) NOT NULL,
  `name` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  PRIMARY KEY (`user_id`, `name`),
  CONSTRAINT `user_setting_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `target` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_team`
--

DROP TABLE IF EXISTS `user_team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_team` (
  `user_id` bigint(20) NOT NULL,
  `team_id` bigint(20) NOT NULL,
  PRIMARY KEY (`user_id`,`team_id`),
  KEY `ix_user_team_team_id` (`team_id`),
  CONSTRAINT `user_team_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`target_id`),
  CONSTRAINT `user_team_ibfk_2` FOREIGN KEY (`team_id`) REFERENCES `team` (`target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


--
-- Table structure for table `application_quotas`
--

DROP TABLE IF EXISTS `application_quota`;
CREATE TABLE `application_quota` (
  `application_id` int(11) NOT NULL,
  `hard_quota_threshold` smallint(5) NOT NULL,
  `soft_quota_threshold` smallint(5) NOT NULL,
  `hard_quota_duration` smallint(5) NOT NULL,
  `soft_quota_duration` smallint(5) NOT NULL,
  `plan_name` varchar(255),
  `target_id` bigint(20),
  `wait_time` smallint(5) NOT NULL DEFAULT 0,
  PRIMARY KEY (`application_id`),
  KEY `application_quota_plan_name_fk_idx` (`plan_name`),
  KEY `application_quota_target_id_fk_idx` (`target_id`),
  CONSTRAINT `application_id_ibfk` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `plan_name_ibfk` FOREIGN KEY (`plan_name`) REFERENCES `plan_active` (`name`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `target_id_ibfk` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`) ON DELETE SET NULL ON UPDATE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


--
-- Table structure for table `application_mode`
--

DROP TABLE IF EXISTS `application_mode`;
CREATE TABLE `application_mode` (
  `application_id` int(11) NOT NULL,
  `mode_id` int(11) NOT NULL,
  PRIMARY KEY (`application_id`, `mode_id`),
  CONSTRAINT `application_mode_application_id_ibfk` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `application_mode_mode_id_ibfk` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `application_owner`
--

DROP TABLE IF EXISTS `application_owner`;
CREATE TABLE `application_owner` (
  `application_id` int(11) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`application_id`, `user_id`),
  CONSTRAINT `application_owner_application_id_ibfk` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `application_owner_user_id_ibfk` FOREIGN KEY (`user_id`) REFERENCES `user` (`target_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `application_custom_sender_address` defines custom "from" addresses
--

DROP TABLE IF EXISTS `application_custom_sender_address`;
CREATE TABLE `application_custom_sender_address` (
  `application_id` int(11) NOT NULL,
  `mode_id` int(11) NOT NULL,
  `sender_address` varchar(255) NOT NULL,
  PRIMARY KEY (`application_id`, `mode_id`),
  CONSTRAINT `application_custom_sender_address_id_ibfk` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `application_custom_sender_address_mode_id_ibfk` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `twilio_delivery_status`
--

DROP TABLE IF EXISTS `twilio_delivery_status`;
CREATE TABLE `twilio_delivery_status` (
  `twilio_sid` varchar(34) NOT NULL,
  `message_id` bigint(20) DEFAULT NULL,
  `status` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`twilio_sid`),
  KEY `twilio_delivery_status_message_id_fk_idx` (`message_id`),
  CONSTRAINT `twilio_delivery_status_message_id_ibfk` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


DROP TABLE IF EXISTS `twilio_retry`;
CREATE TABLE `twilio_retry` (
  `message_id` bigint(20) NOT NULL,
  `retry_id` bigint(20) NOT NULL,
  PRIMARY KEY (`message_id`),
  KEY `twilio_retry_retry_id_fk_idx` (`retry_id`),
  CONSTRAINT `twilio_retry_message_id_ibfk` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `twilio_retry_retry_id_ibfk` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `incident_emails`
--

DROP TABLE IF EXISTS `incident_emails`;
CREATE TABLE `incident_emails` (
  `email` varchar(255) NOT NULL,
  `application_id` int(11) NOT NULL,
  `plan_name` varchar(255) NOT NULL,
  PRIMARY KEY (`email`),
  KEY `incident_emails_plan_name_fk_idx` (`plan_name`),
  KEY `incident_emails_application_id_fk_idx` (`application_id`),
  CONSTRAINT `incident_emails_application_id_ibfk` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `incident_emails_plan_name_ibfk` FOREIGN KEY (`plan_name`) REFERENCES `plan_active` (`name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `generic_message_sent_status`
--

DROP TABLE IF EXISTS `generic_message_sent_status`;
CREATE TABLE `generic_message_sent_status` (
  `message_id` bigint(20) NOT NULL,
  `status` tinyint(1) NOT NULL,
  PRIMARY KEY (`message_id`),
  CONSTRAINT `generic_message_sent_status_message_id_ibfk` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `mailing_list`
--

DROP TABLE IF EXISTS `mailing_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mailing_list` (
  `target_id` bigint(20) NOT NULL,
  `count` bigint(20) NOT NULL DEFAULT 0,
  PRIMARY KEY (`target_id`),
  CONSTRAINT `mailing_list_ibfk_1` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mailing_list_membership`
--

DROP TABLE IF EXISTS `mailing_list_membership`;
CREATE TABLE `mailing_list_membership` (
  `list_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`list_id`, `user_id`),
  CONSTRAINT `mailing_list_membership_list_id_ibfk` FOREIGN KEY (`list_id`) REFERENCES `mailing_list` (`target_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `mailing_list_membership_user_id_ibfk` FOREIGN KEY (`user_id`) REFERENCES `user` (`target_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


DROP TABLE IF EXISTS `device`;
CREATE TABLE `device` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `registration_id` VARCHAR(255) NOT NULL UNIQUE,
  `user_id` BIGINT(20) NOT NULL,
  `platform` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `device_user_id_ibfk` FOREIGN KEY (`user_id`) REFERENCES `user` (`target_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


DROP TABLE IF EXISTS `application_stats`;
CREATE TABLE `application_stats` (
  `application_id` INT(11) NOT NULL,
  `statistic` VARCHAR(255) NOT NULL,
  `value` FLOAT,
  `timestamp` DATETIME NOT NULL,
  PRIMARY KEY (`application_id`, `statistic`, `timestamp`),
  CONSTRAINT `application_stats_app_id_ibfk` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `global_stats`;
CREATE TABLE `global_stats` (
  `statistic` VARCHAR(255) NOT NULL,
  `value` FLOAT,
  `timestamp` DATETIME NOT NULL,
  PRIMARY KEY (`statistic`, `timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `comment`;
CREATE TABLE `comment` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `incident_id` BIGINT(20) NOT NULL,
  `created` DATETIME NOT NULL,
  `user_id` BIGINT(20) NOT NULL,
  `content` TEXT NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `comment_incident_id_ibfk` FOREIGN KEY (`incident_id`) REFERENCES `incident` (`id`),
  CONSTRAINT `comment_user_id_ibfk` FOREIGN KEY (`user_id`) REFERENCES `user` (`target_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `notification_category`;
CREATE TABLE `notification_category` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT,
  `application_id` INT(11) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` VARCHAR(255) NOT NULL,
  `mode_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `notification_category_app_id_ibfk` FOREIGN KEY (`application_id`) REFERENCES `application` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `notification_category_mode_id_ibfk` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`),
  KEY `ix_notification_category_app_id` (`application_id`),
  UNIQUE KEY (`application_id`, `name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `mode_template_override`;
CREATE TABLE `mode_template_override` (
  `target_id` BIGINT(20) NOT NULL,
  `mode_id` INT(11) NOT NULL,
  PRIMARY KEY (`target_id`),
  CONSTRAINT `target_id_override_ibfk_1` FOREIGN KEY (`target_id`) REFERENCES `target` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `mode_id_override_ibfk_1`  FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `category_override`;
CREATE TABLE `category_override` (
  `user_id` BIGINT(20) NOT NULL,
  `category_id` BIGINT(20) NOT NULL,
  `mode_id` INT(11) NOT NULL,
  PRIMARY KEY (`user_id`, `category_id`),
  CONSTRAINT `category_override_user_id_ibfk` FOREIGN KEY (`user_id`) REFERENCES `user` (`target_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `category_override_category_id_ibfk` FOREIGN KEY (`category_id`) REFERENCES `notification_category` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `category_override_mode_id_ibfk` FOREIGN KEY (`mode_id`) REFERENCES `mode` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-09-28 11:52:18
