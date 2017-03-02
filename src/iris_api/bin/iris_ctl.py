#!/usr/bin/env python

# Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
# See LICENSE in the project root for license information.

# -*- coding:utf-8 -*-

from contextlib import contextmanager
from sqlalchemy import create_engine
from pymysql.err import IntegrityError
import ujson
import yaml
import click


@click.group()
@click.pass_context
def iris_ctl(ctx):
    pass


@click.group()
@click.pass_context
def app(ctx):
    pass


iris_ctl.add_command(app)


@click.group('import')
@click.pass_context
def app_import(ctx):
    pass


app.add_command(app_import)


def get_db_conn_from_config(config):
    engine = create_engine(config['db']['conn']['str'] % config['db']['conn']['kwargs'],
                           **config['db']['kwargs'])
    return engine.raw_connection()


@contextmanager
def db_from_config(config):
    engine = create_engine(config['db']['conn']['str'] % config['db']['conn']['kwargs'],
                           **config['db']['kwargs'])
    conn = engine.raw_connection()
    cursor = conn.cursor()
    yield conn, cursor
    cursor.close()
    conn.close()


@click.command()
@click.argument('app')
@click.argument('sample_context')
@click.option('--config', default='./config.yaml')
@click.pass_context
def sample_context(ctx, app, sample_context, config):
    with open(sample_context) as fd:
        sample_ctx = fd.read()
        try:
            ujson.loads(sample_ctx)
        except ValueError as e:
            ctx.fail('Invalid JSON, %s: %s' % (str(e), sample_ctx))

    with open(config, 'r') as config_file:
        config = yaml.safe_load(config_file)

    click.echo('Setting sample contenxt for %s to:\n%s' % (app, sample_ctx))
    click.confirm('Do you want to continue?', abort=True)
    with db_from_config(config) as (conn, cursor):
        cursor.execute('UPDATE `application` SET `sample_context`=%s WHERE `name`=%s;',
                       (sample_ctx, app))
        conn.commit()
    click.echo(click.style('All done!', fg='green'))


app_import.add_command(sample_context)


@click.command()
@click.argument('app')
@click.argument('context_template')
@click.option('--config', default='./config.yaml')
@click.pass_context
def context_template(ctx, app, context_template, config):
    with open(context_template) as fd:
        tpl_content = fd.read()

    with open(config, 'r') as config_file:
        config = yaml.safe_load(config_file)

    click.echo('Setting context template for %s to:\n%s' % (app, tpl_content))
    click.confirm('Do you want to continue?', abort=True)
    with db_from_config(config) as (conn, cursor):
        cursor.execute('UPDATE application SET `context_template`=%s WHERE `name`=%s;',
                       (tpl_content, app))
        conn.commit()
    click.echo(click.style('All done!', fg='green'))


app_import.add_command(context_template)


@click.command()
@click.argument('app')
@click.argument('summary_template')
@click.option('--config', default='./config.yaml')
@click.pass_context
def summary_template(ctx, app, summary_template, config):
    with open(summary_template) as fd:
        tpl_content = fd.read()

    with open(config, 'r') as config_file:
        config = yaml.safe_load(config_file)

    click.echo('Setting summary template for %s to:\n%s' % (app, tpl_content))
    click.confirm('Do you want to continue?', abort=True)

    with db_from_config(config) as (conn, cursor):
        cursor.execute('UPDATE application SET `summary_template`=%s WHERE `name`=%s;',
                       (tpl_content, app))
        conn.commit()
    click.echo(click.style('All done!', fg='green'))


app_import.add_command(summary_template)


@click.group()
@click.pass_context
def template(ctx):
    pass


iris_ctl.add_command(template)


@click.command('delete')
@click.argument('template')
@click.option('--config', default='./config.yaml')
@click.pass_context
def delete_template(ctx, template, config):
    with open(config, 'r') as config_file:
        config = yaml.safe_load(config_file)

    click.echo('Deleting template %s' % template)
    click.confirm('Do you want to continue?', abort=True)

    with db_from_config(config) as (conn, cursor):
        try:
            cursor.execute('DELETE FROM template WHERE `name` = %s', template)
            if cursor.rowcount == 0:
                raise click.ClickException('No template found with given name')
        except IntegrityError as e:
            cursor.execute('''SELECT `message`.`id` FROM
                                  message JOIN template ON `message`.`template_id` = `template`.`id`
                              WHERE template.`name` = %s''', template)
            msgs = cursor.fetchall()
            cursor.execute('''SELECT `plan_id` FROM plan_notification JOIN template
                                  ON `plan_notification`.`template_id` = `template`.`id`
                              WHERE template.`name` = %s''', template)
            plans = cursor.fetchall()

            if msgs:
                click.echo(click.style('Template referenced by messages with ids:\n%s' % [m[0] for m in msgs],
                                       fg='red'),
                           err=True)
            if plans:
                click.echo(click.style('Template referenced by plans with ids:\n%s' % [p[0] for p in plans],
                                       fg='red'),
                           err=True)
            raise click.ClickException('Template referenced by a message/plan; for auditing purposes, delete not allowed')
        except Exception as e:
            raise click.ClickException(str(e))
        else:
            conn.commit()
            click.echo(click.style('All done!', fg='green'))


template.add_command(delete_template)


@click.group()
@click.pass_context
def plan(ctx):
    pass


iris_ctl.add_command(plan)


@click.command('delete')
@click.argument('plan')
@click.option('--config', default='./config.yaml')
@click.pass_context
def delete_plan(ctx, plan, config):
    with open(config, 'r') as config_file:
        config = yaml.safe_load(config_file)

    click.echo('Deleting plan %s' % plan)
    click.confirm('Do you want to continue?', abort=True)

    with db_from_config(config) as (conn, cursor):
        try:
            cursor.execute('DELETE plan_active FROM plan_active JOIN plan ON plan_active.`plan_id` = plan.`id` '
                           'WHERE plan.`name` = %s', plan)
            cursor.execute('DELETE plan_notification '
                           'FROM plan_notification JOIN plan ON plan_notification.`plan_id` = plan.`id` '
                           'WHERE plan.`name` = %s', plan)
            cursor.execute('DELETE FROM plan WHERE `name` = %s', plan)
            if cursor.rowcount == 0:
                raise click.ClickException('No plan found with given name')
        except IntegrityError as e:
            cursor.execute('''SELECT `message`.`id` FROM
                                  message JOIN plan ON `message`.`plan_id` = `plan`.`id`
                              WHERE plan.`name` = %s''', plan)
            msgs = cursor.fetchall()
            cursor.execute('''SELECT incident.`id` FROM incident JOIN plan
                                  ON `incident`.`plan_id` = `plan`.`id`
                              WHERE plan.`name` = %s''', plan)
            incidents = cursor.fetchall()

            if msgs:
                click.echo(click.style('Plan referenced by messages with ids:\n%s' % [m[0] for m in msgs],
                                       fg='red'),
                           err=True)
            if incidents:
                click.echo(click.style('Plan referenced by incidents with ids:\n%s' % [i[0] for i in incidents],
                                       fg='red'),
                           err=True)
            raise click.ClickException('Plan referenced by a message/incident; for auditing purposes, delete not allowed')
        except Exception as e:
            raise click.ClickException(str(e))
        else:
            conn.commit()
            click.echo(click.style('All done!', fg='green'))


plan.add_command(delete_plan)


def main():
    iris_ctl(obj={})


if __name__ == '__main__':
    main()
