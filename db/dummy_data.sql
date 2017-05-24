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

LOCK TABLES `target` WRITE;
INSERT INTO `target` VALUES (1,'demo',1,1),(2,'abc',1,1),(3,'foo',1,1),(4,'demo_team',2,1),(5,'foo_team',2,1),(6,'abc',3,1),(7,'demo',3,1);
UNLOCK TABLES;

LOCK TABLES `user` WRITE;
INSERT INTO `user` VALUES (1, 1),(2, 0),(3, 0);
UNLOCK TABLES;

LOCK TABLES `application` WRITE;
INSERT INTO `application` VALUES
    (8,'Autoalerts','a7a9d7657ac8837cd7dfed0b93f4b8b864007724d7fa21422c24f4ff0adb2e49','{{#context}}\n<div style=\"text-align: center;\">\n    <a href=\"{{console_url}}\" style=\"margin-right: 10px;\">{{name}}</a>\n    <div style=\"margin-bottom: 10px;\">\n      <small>\n        <span style=\"margin-right: 10px;\">\n          <span class=\"light\">Datacenter:</span> {{fabric}}\n        </span>\n        <span>\n          <span class=\"light\">Zones:</span> {{zones}}\n        </span>\n      </small>\n    </div>\n    {{#if nodes}}\n      <p><small><span class=\"light\">Nodes:</span> {{#each nodes}} {{this}} {{/each}}</small></p>\n    {{/if}}\n    {{#if notes}}\n      <p>Notes: {{notes}}</p>\n    {{/if}}\n  </div>\n</div>\n{{/context}}','{{#context}}\n<ul>\n  {{#if name}}\n    <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{name}}\">\n      <strong> Name: </strong> {{name}}\n    </li>\n  {{/if}}\n  {{#if filename}}\n    <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{filename}}\">\n      <strong> Dashboard: </strong> {{filename}}\n    </li>\n  {{/if}}\n  {{#if fabric}}\n    <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{fabric}}\">\n      <strong>Fabric: </strong> {{fabric}}\n    </li>\n  {{/if}}\n  {{#if zones}}\n   <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{zones}}\">\n    <strong>Zones: </strong> {{zones}}\n   </li>\n  {{/if}}\n  {{#if nodes}}\n    <li>\n      <strong>Nodes: </strong>\n      <ul>\n        {{#each nodes}}\n          <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{this}}\"> {{this}} </li>\n        {{/each}}\n      </ul>\n    </li>\n  {{/if}}\n</ul>\n{{/context}}\n','{\n  \"console_url\": \"\",\n  \"fabric\": \"DC1\",\n  \"filename\": \"dashboard\",\n  \"graph_image_url\": \"http://url.example.com/foo\",\n  \"metanodes\": [\n    [\"execution_time.metanode1\", \"threshold: 72 is greater than the max (65)\"]\n  ],\n  \"name\": \"Name Of Your Alert\",\n  \"nodes\": [\n    [\"execution_time.server1.example.com\", \"threshold: 72 is greater than the max (65)\"]\n  ],\n  \"notes\": \"This is a note\",\n  \"zones\": [\"zone1\", \"zone2\"]\n}',0,0, 0),
    (10,'test-app','sdffdssdf',NULL,NULL,NULL,0,0, 0),
    (11,'iris','fooooo',NULL,NULL,NULL,1,1,1);
UNLOCK TABLES;

LOCK TABLES `default_application_mode` WRITE;
UNLOCK TABLES;

LOCK TABLES `incident` WRITE;
UNLOCK TABLES;

LOCK TABLES `message` WRITE;
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
    (38,'demo-test-incident-post','2017-01-25 23:30:34',1,NULL,'Test plan for e2e test',1,900,10,300,300,NULL,NULL,NULL);
UNLOCK TABLES;

LOCK TABLES `plan_active` WRITE;
INSERT INTO `plan_active` VALUES
    ('demo-test-foo',31),
    ('demo-test-incident-post',38);
UNLOCK TABLES;

LOCK TABLES `template` WRITE;
INSERT INTO `template` VALUES
    (12,'test_template','2017-01-25 15:26:45',1),
    (13,'test_template','2017-01-25 15:30:35',1);
UNLOCK TABLES;

LOCK TABLES `template_active` WRITE;
INSERT INTO `template_active` VALUES ('test_template',13);
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
    (13,8,35,'email_subject','email_body',NULL,NULL,NULL,NULL,NULL,NULL);
UNLOCK TABLES;

LOCK TABLES `template_variable` WRITE;
INSERT INTO `template_variable` VALUES
    (1,8,'fabric',0),
    (2,8,'console_url',0),
    (3,8,'filename',0),
    (4,8,'name',0),
    (5,8,'graph_image_url',0),
    (7,8,'zones',0),
    (8,8,'nodes',0),
    (9,8,'metanodes',0),
    (10,8,'notes',0);
UNLOCK TABLES;

LOCK TABLES `plan_notification` WRITE;
INSERT INTO `plan_notification` VALUES
    (1,1,1,'test_template',4,44,17,1,300),
    (2,1,1,'test_template',4,35,35,0,600),
    (3,1,2,'test_template',4,35,26,0,600),
    (4,1,2,'test_template',4,44,8,1,300),
    (5,7,1,'test_template',4,35,35,0,600),
    (6,7,1,'test_template',4,44,17,1,300),
    (7,8,1,'test_template',4,35,35,0,600),
    (9,11,1,'test_template',4,44,17,1,300),
    (10,11,1,'test_template',4,35,35,0,600),
    (11,11,2,'test_template',4,35,26,0,600),
    (12,11,2,'test_template',4,44,8,1,300),
    (13,17,1,'test_template',4,35,35,0,600),
    (14,17,1,'test_template',4,44,17,1,300),
    (15,18,1,'test_template',4,35,35,0,600),
    (17,21,1,'test_template',4,44,17,1,300),
    (18,21,1,'test_template',4,35,35,0,600),
    (19,21,2,'test_template',4,35,26,0,600),
    (20,21,2,'test_template',4,44,8,1,300),
    (21,27,1,'test_template',4,35,35,0,600),
    (22,27,1,'test_template',4,44,17,1,300),
    (23,28,1,'test_template',4,35,35,0,600),
    (25,31,1,'test_template',4,44,17,1,300),
    (26,31,1,'test_template',4,35,35,0,600),
    (27,31,2,'test_template',4,35,26,0,600),
    (28,31,2,'test_template',4,44,8,1,300),
    (29,37,1,'test_template',4,35,35,0,600),
    (30,37,1,'test_template',4,44,17,1,300),
    (31,38,1,'test_template',4,35,35,0,600);
UNLOCK TABLES;

LOCK TABLES `response` WRITE;
UNLOCK TABLES;

LOCK TABLES `target_application_mode` WRITE;
INSERT INTO `target_application_mode` VALUES (1,8,26,26);
UNLOCK TABLES;

LOCK TABLES `target_contact` WRITE;
INSERT INTO `target_contact` VALUES
    (1,8,'+1 407-456-7891'),(1,17,'demo1'),(1,26,'+1 407-456-7891'),(1,35,'demo1@foo.bar'),
    (2,8,'+1 407-456-7892'),(2,17,'demo2'),(2,26,'+1 407-456-7892'),(2,35,'demo2@foo.bar'),
    (3,8,'+1 407-456-7893'),(3,17,'demo3'),(3,26,'+1 407-456-7893'),(3,35,'demo3@foo.bar');
UNLOCK TABLES;

LOCK TABLES `target_mode` WRITE;
INSERT INTO `target_mode` VALUES (1,26,26);
UNLOCK TABLES;

LOCK TABLES `target_reprioritization` WRITE;
UNLOCK TABLES;

LOCK TABLES `team` WRITE;
UNLOCK TABLES;

LOCK TABLES `user_setting` WRITE;
UNLOCK TABLES;

LOCK TABLES `user_team` WRITE;
UNLOCK TABLES;

INSERT IGNORE INTO `application_mode` (`application_id`, `mode_id`) SELECT `application`.`id`, `mode`.`id` FROM `application`, `mode` WHERE `mode`.`name` != 'drop';
