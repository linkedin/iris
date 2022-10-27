SINGLE_PLAN_QUERY = '''SELECT `plan`.`id` as `id`, `plan`.`name` as `name`,
    `plan`.`threshold_window` as `threshold_window`, `plan`.`threshold_count` as `threshold_count`,
    `plan`.`aggregation_window` as `aggregation_window`, `plan`.`aggregation_reset` as `aggregation_reset`,
    `plan`.`description` as `description`, UNIX_TIMESTAMP(`plan`.`created`) as `created`,
    `target`.`name` as `creator`, IF(`plan_active`.`plan_id` IS NULL, FALSE, TRUE) as `active`,
    `plan`.`tracking_type` as `tracking_type`, `plan`.`tracking_key` as `tracking_key`,
    `plan`.`tracking_template` as `tracking_template`
FROM `plan` JOIN `target` ON `plan`.`user_id` = `target`.`id`
LEFT OUTER JOIN `plan_active` ON `plan`.`id` = `plan_active`.`plan_id`'''

SINGLE_PLAN_QUERY_STEPS = '''SELECT `plan_notification`.`id` as `id`,
    `plan_notification`.`step` as `step`,
    `plan_notification`.`repeat` as `repeat`,
    `plan_notification`.`wait` as `wait`,
    `plan_notification`.`optional` as `optional`,
    `target_role`.`name` as `role`,
    `target`.`name` as `target`,
    `plan_notification`.`template` as `template`,
    `priority`.`name` as `priority`,
    `plan_notification`.`dynamic_index` AS `dynamic_index`
FROM `plan_notification`
LEFT OUTER JOIN `target` ON `plan_notification`.`target_id` = `target`.`id`
LEFT OUTER JOIN `target_role` ON `plan_notification`.`role_id` = `target_role`.`id`
JOIN `priority` ON `plan_notification`.`priority_id` = `priority`.`id`
WHERE `plan_notification`.`plan_id` = %s
ORDER BY `plan_notification`.`step`'''
