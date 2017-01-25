LOCK TABLES `target_type` WRITE;
INSERT IGNORE INTO `target_type` VALUES (2,'team'),(1,'user');
UNLOCK TABLES;

LOCK TABLES `target` WRITE;
INSERT IGNORE INTO `target` VALUES (1,'demo',1,1),(2,'abc',1,1),(3,'foo',1,1),(4,'demo_team',2,1),(5,'foo_team',2,1);
UNLOCK TABLES;

LOCK TABLES `user` WRITE;
INSERT IGNORE INTO `user` VALUES (1),(2),(3);
UNLOCK TABLES;

LOCK TABLES `mode` WRITE;
INSERT IGNORE INTO `mode` VALUES (26,'call'),(35,'email'),(17,'im'),(8,'sms');
UNLOCK TABLES;

LOCK TABLES `priority` WRITE;
INSERT IGNORE INTO `priority` VALUES (8,'urgent',26),(17,'high',8),(26,'medium',35),(35,'low',35);
UNLOCK TABLES;

LOCK TABLES `target_role` WRITE;
INSERT IGNORE INTO `target_role` VALUES (8,'user',1),(17,'manager',1),(35,'team',2),(44,'oncall',2);
UNLOCK TABLES;

LOCK TABLES `target_contact` WRITE;
INSERT IGNORE INTO `target_contact` VALUES (1,8,'+1 123-456-7890'),(1,17,'demo'),(1,26,'+1 123-456-7890'),(1,35,'demo@foo.bar');
UNLOCK TABLES;

LOCK TABLES `application` WRITE;
INSERT INTO `application` VALUES (8,'Autoalerts','a7a9d7657ac8837cd7dfed0b93f4b8b864007724d7fa21422c24f4ff0adb2e49','{{#context}}\n<div style=\"text-align: center;\">\n    <a href=\"{{console_url}}\" style=\"margin-right: 10px;\">{{name}}</a>\n    <div style=\"margin-bottom: 10px;\">\n      <small>\n        <span style=\"margin-right: 10px;\">\n          <span class=\"light\">Datacenter:</span> {{fabric}}\n        </span>\n        <span>\n          <span class=\"light\">Zones:</span> {{zones}}\n        </span>\n      </small>\n    </div>\n    {{#if nodes}}\n      <p><small><span class=\"light\">Nodes:</span> {{#each nodes}} {{this}} {{/each}}</small></p>\n    {{/if}}\n    {{#if notes}}\n      <p>Notes: {{notes}}</p>\n    {{/if}}\n  </div>\n</div>\n{{/context}}','{{#context}}\n<ul>\n  {{#if name}}\n    <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{name}}\">\n      <strong> Name: </strong> {{name}}\n    </li>\n  {{/if}}\n  {{#if filename}}\n    <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{filename}}\">\n      <strong> Dashboard: </strong> {{filename}}\n    </li>\n  {{/if}}\n  {{#if fabric}}\n    <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{fabric}}\">\n      <strong>Fabric: </strong> {{fabric}}\n    </li>\n  {{/if}}\n  {{#if zones}}\n   <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{zones}}\">\n    <strong>Zones: </strong> {{zones}}\n   </li>\n  {{/if}}\n  {{#if nodes}}\n    <li>\n      <strong>Nodes: </strong>\n      <ul>\n        {{#each nodes}}\n          <li data-toggle=\"tooltip\" data-placement=\"top\" title=\"{{this}}\"> {{this}} </li>\n        {{/each}}\n      </ul>\n    </li>\n  {{/if}}\n</ul>\n{{/context}}\n','{\n  \"console_url\": \"\",\n  \"fabric\": \"DC1\",\n  \"filename\": \"dashboard\",\n  \"graph_image_url\": \"http://url.example.com/foo\",\n  \"metanodes\": [\n    [\"execution_time.metanode1\", \"threshold: 72 is greater than the max (65)\"],\n  ],\n  \"name\": \"Name Of Your Alert\",\n  \"nodes\": [\n    [\"execution_time.server1.example.com\", \"threshold: 72 is greater than the max (65)\"],\n  ],\n  \"notes\": \"This is a note\",\n  \"zones\": [\"zone1\", \"zone2\"]\n}',0,0),(9,'iris-frontend','fooooo',NULL,NULL,NULL,1,1),(10,'test-app','sdffdssdf',NULL,NULL,NULL,0,0);
UNLOCK TABLES;

LOCK TABLES `template_variable` WRITE;
INSERT INTO `template_variable` VALUES (1,8,'fabric',0),(2,8,'console_url',0),(3,8,'filename',0),(4,8,'name',0),(5,8,'graph_image_url',0),(7,8,'zones',0),(8,8,'nodes',0),(9,8,'metanodes',0),(10,8,'notes',0);
UNLOCK TABLES;
