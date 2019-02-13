/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
-- DEFAULT DB VALUES
LOCK TABLES `mode` WRITE;
INSERT INTO `mode` VALUES (26,'call'),(35,'email'),(17,'slack'),(8,'sms'),(36,'drop');
UNLOCK TABLES;

LOCK TABLES `priority` WRITE;
INSERT INTO `priority` VALUES (8,'urgent',26),(17,'high',8),(26,'medium',35),(35,'low',35);
UNLOCK TABLES;

LOCK TABLES `target_type` WRITE;
INSERT INTO `target_type` VALUES (3,'mailing-list'),(2,'team'),(1,'user');
UNLOCK TABLES;

LOCK TABLES `target_role` WRITE;
INSERT INTO `target_role` VALUES
    (8,'user',1),
    (17,'manager',2),
    (35,'team',2),
    (44,'oncall-primary',2),
    (45,'oncall-secondary',2);
UNLOCK TABLES;

-- END DEFAULT DB VALUES

LOCK TABLES `application` WRITE;
INSERT INTO `application` VALUES
    (8,'Autoalerts','a7a9d7657ac8837cd7dfed0b93f4b8b864007724d7fa21422c24f4ff0adb2e49','{{#context}}\n<div style=\"text-align: center;\">\n    <a href=\"{{console_url}}\" style=\"margin-right: 10px;\">{{name}}</a>\n    <div style=\"margin-bottom: 10px;\">\n      <small>\n        <span style=\"margin-right: 10px;\">\n          <span class=\"light\">Datacenter:</span> {{fabric}}\n        </span>\n        <span>\n          <span class=\"light\">Zones:</span> {{zones}}\n        </span>\n      </small>\n    </div>\n    {{#if nodes}}\n      <p><small><span class=\"light\">Nodes:</span> {{#each nodes}} {{this}} {{/each}}</small></p>\n    {{/if}}\n    {{#if notes}}\n      <p>Notes: {{notes}}</p>\n    {{/if}}\n  </div>\n</div>\n{{/context}}','{{#context}}\n<ul>\n  {{#if name}}\n    <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{name}}\">\n      <strong> Name: </strong> {{name}}\n    </li>\n  {{/if}}\n  {{#if filename}}\n    <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{filename}}\">\n      <strong> Dashboard: </strong> {{filename}}\n    </li>\n  {{/if}}\n  {{#if fabric}}\n    <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{fabric}}\">\n      <strong>Fabric: </strong> {{fabric}}\n    </li>\n  {{/if}}\n  {{#if zones}}\n   <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{zones}}\">\n    <strong>Zones: </strong> {{zones}}\n   </li>\n  {{/if}}\n  {{#if nodes}}\n    <li>\n      <strong>Nodes: </strong>\n      <ul>\n        {{#each nodes}}\n          <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{this}}\"> {{this}} </li>\n        {{/each}}\n      </ul>\n    </li>\n  {{/if}}\n</ul>\n{{/context}}\n','{\n  \"console_url\": \"\",\n  \"fabric\": \"DC1\",\n  \"filename\": \"dashboard\",\n  \"graph_image_url\": \"http://url.example.com/foo\",\n  \"metanodes\": [\n    [\"execution_time.metanode1\", \"threshold: 72 is greater than the max (65)\"]\n  ],\n  \"name\": \"Name Of Your Alert\",\n  \"nodes\": [\n    [\"execution_time.server1.example.com\", \"threshold: 72 is greater than the max (65)\"]\n  ],\n  \"notes\": \"This is a note\",\n  \"zones\": [\"zone1\", \"zone2\"]\n}',NULL,0,0,0,NULL),
    (10,'test-app','sdffdssdf',NULL,NULL,NULL,NULL,0,0,0,NULL),
    (11,'iris','fooooo',NULL,NULL,NULL,NULL,1,1,1,NULL),
    (12,'oncall','magic','','','{}',NULL,0,0,0,NULL);
UNLOCK TABLES;

LOCK TABLES `application_mode` WRITE;
INSERT INTO `application_mode` VALUES
    (8,8),
    (8,17),
    (8,26),
    (8,35),
    (10,8),
    (10,17),
    (10,26),
    (10,35),
    (11,8),
    (11,17),
    (11,26),
    (11,35),
    (12,8),
    (12,17),
    (12,26),
    (12,35);
UNLOCK TABLES;

LOCK TABLES `application_owner` WRITE;
UNLOCK TABLES;

LOCK TABLES `application_quota` WRITE;
UNLOCK TABLES;

LOCK TABLES `default_application_mode` WRITE;
UNLOCK TABLES;

LOCK TABLES `dynamic_plan_map` WRITE;
UNLOCK TABLES;

LOCK TABLES `generic_message_sent_status` WRITE;
UNLOCK TABLES;

LOCK TABLES `incident` WRITE;
INSERT INTO `incident` VALUES
    (1,40,'2017-01-25 23:22:55','2017-01-25 23:24:55','{\"console_url\": \"\", \"fabric\": \"DC1\", \"notes\": \"This is a note\", \"filename\": \"dashboard\", \"zones\": [\"zone1\", \"zone2\"], \"metanodes\": [[\"execution_time.metanode1\", \"threshold: 72 is greater than the max (65)\"]], \"nodes\": [[\"execution_time.server1.example.com\", \"threshold: 72 is greater than the max (65)\"]], \"graph_image_url\": \"http://url.example.com/foo\", \"name\":\"API Alert\"}',1,8,1,0),
    (2,40,'2017-01-25 23:22:55','2017-01-25 23:24:55','{\"console_url\": \"\", \"fabric\": \"DC1\", \"notes\": \"This is a note\", \"filename\": \"dashboard\", \"zones\": [\"zone1\", \"zone2\"], \"metanodes\": [[\"execution_time.metanode1\", \"threshold: 72 is greater than the max (65)\"]], \"nodes\": [[\"execution_time.server1.example.com\", \"threshold: 72 is greater than the max (65)\"]], \"graph_image_url\": \"http://url.example.com/foo\", \"name\":\"API Alert\"}',1,8,1,0),
    (3,40,'2017-01-25 23:22:55','2017-01-25 23:24:55','{\"console_url\": \"\", \"fabric\": \"DC1\", \"notes\": \"This is a note\", \"filename\": \"dashboard\", \"zones\": [\"zone1\", \"zone2\"], \"metanodes\": [[\"execution_time.metanode1\", \"threshold: 72 is greater than the max (65)\"]], \"nodes\": [[\"execution_time.server1.example.com\", \"threshold: 72 is greater than the max (65)\"]], \"graph_image_url\": \"http://url.example.com/foo\", \"name\":\"API Alert\"}',1,8,1,0);
UNLOCK TABLES;

LOCK TABLES `incident_emails` WRITE;
UNLOCK TABLES;

LOCK TABLES `mailing_list` WRITE;
UNLOCK TABLES;

LOCK TABLES `mailing_list_membership` WRITE;
UNLOCK TABLES;

LOCK TABLES `message` WRITE;
INSERT INTO `message` VALUES
    (1,NULL,'2017-01-25 23:23:55','2017-01-25 23:24:55',8,1,'demo1@foo.bar',35,40,35,'email_subject','email_body',1,33,0,13),
    (2,'10018616db1e4cceba3a9f69177c2343','2017-01-29 23:23:55','2017-01-25 23:24:55',8,1,'demo1@foo.bar',35,40,35,'email_subject','email_body',2,33,0,13),
    (3,'10018616db1e4cceba3a9f69177c2343','2017-01-29 23:23:55','2017-01-25 23:24:55',8,1,'demo1@foo.bar',35,40,35,'email_subject','email_body',3,33,0,13);
UNLOCK TABLES;

LOCK TABLES `message_changelog` WRITE;
UNLOCK TABLES;

LOCK TABLES `plan` WRITE;
INSERT INTO `plan` VALUES
    (1,'demo-test-foo','2017-01-25 23:23:55',1,NULL,'Test plan for e2e test',2,900,10,300,300,NULL,NULL,NULL),
    (7,'demo-test-incident-post','2017-01-25 23:23:55',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL),
    (8,'demo-test-incident-post','2017-01-25 23:23:56',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL),
    (11,'demo-test-foo','2017-01-25 23:25:46',1,NULL,'Test plan for e2e test',2,900,10,300,300,NULL,NULL,NULL),
    (17,'demo-test-incident-post','2017-01-25 23:25:46',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL),
    (18,'demo-test-incident-post','2017-01-25 23:25:46',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL),
    (21,'demo-test-foo','2017-01-25 23:26:44',1,NULL,'Test plan for e2e test',2,900,10,300,300,NULL,NULL,NULL),
    (27,'demo-test-incident-post','2017-01-25 23:26:44',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL),
    (28,'demo-test-incident-post','2017-01-25 23:26:45',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL),
    (31,'demo-test-foo','2017-01-25 23:30:34',1,NULL,'Test plan for e2e test',2,900,10,300,300,NULL,NULL,NULL),
    (37,'demo-test-incident-post','2017-01-25 23:30:34',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL),
    (38,'demo-test-incident-post','2017-01-25 23:30:34',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL),
    (39,'demo-test-other-app-incident-post','2017-01-25 23:30:34',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL),
    (40,'demo-test-bar','2017-01-25 23:25:46',1,NULL,'Test plan for e2e email incident test',1,900,10,300,300,NULL,NULL,NULL),
    (41,'Oncall test','2018-01-26 22:32:04',1,NULL,'Test plan for Oncall Iris integration',1,900,10,300,300,NULL,NULL,NULL);
UNLOCK TABLES;

LOCK TABLES `plan_active` WRITE;
INSERT INTO `plan_active` VALUES
    ('demo-test-foo',31),
    ('demo-test-incident-post',38),
    ('demo-test-other-app-incident-post',39),
    ('demo-test-bar',40),
    ('Oncall test',41);
UNLOCK TABLES;

LOCK TABLES `plan_notification` WRITE;
INSERT INTO `plan_notification` VALUES
    (1,1,1,'test_template',4,0,44,17,1,300,NULL),
    (2,1,1,'test_template',4,0,35,35,0,600,NULL),
    (3,1,2,'test_template',4,0,35,26,0,600,NULL),
    (4,1,2,'test_template',4,0,44,8,1,300,NULL),
    (5,7,1,'test_template',4,0,35,35,0,600,NULL),
    (6,7,1,'test_template',4,0,44,17,1,300,NULL),
    (7,8,1,'test_template',4,0,35,35,0,600,NULL),
    (9,11,1,'test_template',4,0,44,17,1,300,NULL),
    (10,11,1,'test_template',4,0,35,35,0,600,NULL),
    (11,11,2,'test_template',4,0,35,26,0,600,NULL),
    (12,11,2,'test_template',4,0,44,8,1,300,NULL),
    (13,17,1,'test_template',4,0,35,35,0,600,NULL),
    (14,17,1,'test_template',4,0,44,17,1,300,NULL),
    (15,18,1,'test_template',4,0,35,35,0,600,NULL),
    (17,21,1,'test_template',4,0,44,17,1,300,NULL),
    (18,21,1,'test_template',4,0,35,35,0,600,NULL),
    (19,21,2,'test_template',4,0,35,26,0,600,NULL),
    (20,21,2,'test_template',4,0,44,8,1,300,NULL),
    (21,27,1,'test_template',4,0,35,35,0,600,NULL),
    (22,27,1,'test_template',4,0,44,17,1,300,NULL),
    (23,28,1,'test_template',4,0,35,35,0,600,NULL),
    (25,31,1,'test_template',4,0,44,17,1,300,NULL),
    (26,31,1,'test_template',4,0,35,35,0,600,NULL),
    (27,31,2,'test_template',4,0,35,26,0,600,NULL),
    (28,31,2,'test_template',4,0,44,8,1,300,NULL),
    (29,37,1,'test_template',4,0,35,35,0,600,NULL),
    (30,37,1,'test_template',4,0,44,17,1,300,NULL),
    (31,38,1,'test_template',4,0,35,35,0,600,NULL),
    (32,39,1,'test_template_2',4,0,35,35,0,600,NULL),
    (33,40,1,'test_template',4,0,35,35,0,600,NULL),
    (34,41,1,'oncall-test',NULL,0,NULL,26,0,0,2),
    (35,41,1,'oncall-test',NULL,0,NULL,26,0,0,1),
    (36,41,1,'oncall-test',NULL,0,NULL,8,0,0,0);
UNLOCK TABLES;

LOCK TABLES `response` WRITE;
UNLOCK TABLES;

LOCK TABLES `target` WRITE;
INSERT INTO `target` VALUES
    (1,'demo',1,1),
    (2,'abc',1,1),
    (3,'foo',1,1),
    (4,'demo_team',2,1),
    (5,'foo_team',2,1),
    (6,'abc',3,1),
    (7,'demo',3,1);
UNLOCK TABLES;

LOCK TABLES `mailing_list_membership` WRITE;
INSERT INTO `mailing_list_membership` VALUES
    (7,1);
UNLOCK TABLES;

LOCK TABLES `target_application_mode` WRITE;
INSERT INTO `target_application_mode` VALUES
    (1,8,26,26);
UNLOCK TABLES;

LOCK TABLES `target_contact` WRITE;
INSERT INTO `target_contact` VALUES
    (1,8,'+1 223-456-7890'),
    (1,17,'demo1'),
    (1,26,'+1 223-456-7890'),
    (1,35,'demo1@foo.bar'),
    (2,8,'+1 223-456-7891'),
    (2,17,'demo2'),
    (2,26,'+1 223-456-7891'),
    (2,35,'demo2@foo.bar'),
    (3,8,'+1 223-456-7892'),
    (3,17,'demo3'),
    (3,26,'+1 223-456-7892'),
    (3,35,'demo3@foo.bar');
UNLOCK TABLES;

LOCK TABLES `target_mode` WRITE;
INSERT INTO `target_mode` VALUES
    (1,26,26);
UNLOCK TABLES;

LOCK TABLES `target_reprioritization` WRITE;
UNLOCK TABLES;

LOCK TABLES `team` WRITE;
UNLOCK TABLES;

LOCK TABLES `template` WRITE;
INSERT INTO `template` VALUES
    (12,'test_template','2017-01-25 15:26:45',1),
    (13,'test_template','2017-01-25 15:30:35',1),
    (14,'test_template_2','2017-01-25 15:30:35',1),
    (15,'oncall-test','2018-01-26 14:31:19',1);
UNLOCK TABLES;

LOCK TABLES `template_active` WRITE;
INSERT INTO `template_active` VALUES
    ('test_template',13),
    ('test_template_2',14),
    ('oncall-test',15);
UNLOCK TABLES;

LOCK TABLES `template_content` WRITE;
INSERT INTO `template_content` VALUES
    (12,8,8,'','a',NULL,NULL,NULL,NULL,NULL,NULL),
    (12,8,17,'','b',NULL,NULL,NULL,NULL,NULL,NULL),
    (12,8,26,'','c',NULL,NULL,NULL,NULL,NULL,NULL),
    (12,8,35,'email_subject','d',NULL,NULL,NULL,NULL,NULL,NULL),
    (13,8,8,'','test_sms',NULL,NULL,NULL,NULL,NULL,NULL),
    (13,8,17,'','test_slack',NULL,NULL,NULL,NULL,NULL,NULL),
    (13,8,26,'','test_call',NULL,NULL,NULL,NULL,NULL,NULL),
    (13,8,35,'email_subject','email_body',NULL,NULL,NULL,NULL,NULL,NULL),
    (14,10,35,'email_subject','email_body',NULL,NULL,NULL,NULL,NULL,NULL),
    (15,12,8,'','{{requester}} reports: {{description}}',NULL,NULL,NULL,NULL,NULL,NULL),
    (15,12,17,'','{{requester}} reports: {{description}}',NULL,NULL,NULL,NULL,NULL,NULL),
    (15,12,26,'','{{requester}} reports: {{description}}',NULL,NULL,NULL,NULL,NULL,NULL),
    (15,12,35,'Oncall escalation','{{requester}} reports: {{description}}',NULL,NULL,NULL,NULL,NULL,NULL);
UNLOCK TABLES;

LOCK TABLES `template_variable` WRITE;
INSERT INTO `template_variable` VALUES
    (1,8,'fabric',0, 0),
    (2,8,'console_url',0, 0),
    (3,8,'filename',0, 0),
    (4,8,'name',0, 0),
    (5,8,'graph_image_url',0, 0),
    (7,8,'zones',0, 0),
    (8,8,'nodes',0, 0),
    (9,8,'metanodes',0, 0),
    (10,8,'notes',0, 0),
    (11,12,'description',0, 0),
    (12,12,'requester',0, 0);
UNLOCK TABLES;

LOCK TABLES `twilio_delivery_status` WRITE;
UNLOCK TABLES;

LOCK TABLES `twilio_retry` WRITE;
UNLOCK TABLES;

LOCK TABLES `user` WRITE;
INSERT INTO `user` VALUES
    (1,1),
    (2,0),
    (3,0);
UNLOCK TABLES;

LOCK TABLES `user_setting` WRITE;
UNLOCK TABLES;

LOCK TABLES `user_team` WRITE;
UNLOCK TABLES;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
