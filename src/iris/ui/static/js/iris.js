/*
  Copyright (c) LinkedIn Corporation. All rights reserved. Licensed under the BSD-2 Clause license.
  See LICENSE in the project root for license information.
*/

window.iris = window.iris || {}; //define iris app obj

iris = {
  data: {tableEntryLimit: 500},
  init: function(){
    $.fn.dataTableExt.classes.sLengthSelect = "form-control border-bottom";
    window.addEventListener('popstate', this.route.bind(this));
    this.registerHandlebarHelpers();
    $('.main').tooltip({
      selector: '[data-toggle="tooltip"]'
    });
    this.route();
  },
  route: function() {
    // break path into segments and route
    var path = window.location.pathname;
    var start = 0;
    var end = path.length - 1;
    if (path.indexOf('/') == start) {
      start++;
    }
    if (path.lastIndexOf('/') == end) {
      end--;
    }
    path = path.substr(start, end);
    var segments = path.split('/');
    var base_route = segments[0];
    if (!(base_route in this)) {
      return;
    }
    switch (segments.length) {
      case 1:
          this[base_route].init();
        break;
      case 2:
          // Add exception for unsubscribe, which has no plural/singular but requires an app
          if (base_route === 'unsubscribe') {
            this.unsubscribe.init();
          } else {
            this[base_route.slice(0, -1)].init();
          }
        break;
    }
  },
  changeTitle: function(title) {
    window.document.title = (title ? title + ' - ' : '') + 'Iris';
  },
  plans: {
    initialized: false,
    data: {
      url: '/v0/plans',
      $page: $('.main'),
      $table: $('#plans-table'),
      $filterForm: $('#filter-form'),
      tableTemplate: $('#plans-table-template').html(),
      DataTable: null,
      dataTableOpts: {
        orderClasses: false,
        order: [[2, 'desc']],
        columns: [
          { width: '40%' },
          null,
          null,
          null
        ]
      }
    },
    init: function(){
      iris.changeTitle('Plans');
      if (this.initialized == false) {
        this.initFilters();
        this.events();
        this.initialized = true;
      }
      iris.tables.filterTable.call(this);
    },
    events: function(){
      var data = this.data,
          $table = data.$table;

      $table.on('click', 'tbody tr[data-route]', function(e){
        if (e.target.tagName !== 'A') {
          if ((e.ctrlKey || e.metaKey)) {
            window.open('/plans/' + $(this).attr('data-route'));
          } else {
            window.location = '/plans/' + $(this).attr('data-route');
          }
        }
      });
      data.$filterForm.on('submit', iris.tables.filterTable.bind(this));

      //javascript live filtering if needed
      // $page.find('#filter-name').on('keyup', function(){
      //   data.DataTable.column('.name').search($(this).val()).draw();
      // });
      // $page.find('#filter-creator').on('keyup', function(){
      //   data.DataTable.column('.creator').search($(this).val()).draw();
      // });
      // $page.find('#filter-active').on('change', function(){
      //   var state = $(this).prop('checked');
      //   if (state) {
      //     data.DataTable.column('.active').search(state).draw();
      //   } else {
      //     data.DataTable.column('.active').search(state).draw();
      //   }
      // });
    },
    getData: function(params){
      params['limit'] = iris.data.tableEntryLimit;
      return $.getJSON(this.data.url, params).fail(function(){
        iris.createAlert('No plans found');
      });
    },
    initFilters: function(){
      iris.typeahead.init('user');
      $('.datetimepicker').datetimepicker({
        showClose: true,
        keyBinds: {'delete': null}
      });
    }
  }, //end iris.plans
  plan: {
    data: {
      url: '/v0/plans/',
      modesUrl: '/v0/modes',
      $page: $('.plan-details'),
      pageTemplateSource: $('#plan-module-template').html(),
      notificationTemplateSource: $('#plan-notification-template').html(),
      stepTemplateSource: $('#plan-step-template').html(),
      trackingTemplateSource: $('#plan-tracking-notification-template').html(),
      testPlanTemplateSource: $('#test-plan-template').html(),
      addNotificationBtn: '.plan-notification-add',
      removeNotificationBtn: '.plan-notification-remove',
      planNotificationInputs: '.plan-notification input, .plan-notification select',
      addStepBtn: '#add-step',
      addTrackingTemplateBtn: '#add-tracking-template',
      removeStepBtn: '.remove-step',
      removeTrackingTemplateBtn: '.remove-tracking-template',
      createPlanBtn: '#publish-plan',
      clonePlanBtn: '#clone-plan',
      showTestPlanModalBtn: '#test-plan-modal-btn',
      showDeletePlanModalBtn: '#delete-plan-modal-btn',
      toggleDynamic: '.toggle-dynamic',
      testPlanBtn: '#test-plan',
      testPlanInputs: '.test-plan-dynamic-target select',
      deletePlanBtn: '#delete-plan',
      versionSelect: '.version-select',
      activatePlan: '.badge[data-active="0"]',
      viewRelated: '.view-related',
      relatedPlans: [],
      aggregationBtn: '#aggregation h4',
      trackingType: '#tracking-type',
      trackingKey: '#tracking-key',
      trackingTemplateBtn: '#tracking-notification[data-view="false"] .tracking-inner h4',
      variablesTemplateSource: $('#variables-template').html(),
      appSelect: '.template-application',
      countInput: '.notification-count',
      waitInput: '.notification-wait',
      template: null,
      ajaxResponse: null,
      submitModel: {},
      blankModel: {
        modes: null,
        priorities: window.appData.priorities,
        target_roles: window.appData.target_roles,
        availableTemplates: [],
        aggregation_reset: 300,
        aggregation_window: 300,
        threshold_count: 10,
        threshold_window: 900,
        dynamic_index: 0,
        dynamic: 0,
        count: 1,
        optional: 0,
        steps: [[{count: 1, id: 'n0', dynamic_index: 0}]]
      },
      blankTrackingTemplateModel: {
        applications: window.appData.applications,
        modes: null,
        viewMode: false,
        tracking_template: {
          application: {
            email_subject: "",
            email_text: "",
            email_html: "",
            body: ""
          }
        }
      }
    },
    init: function(){
      var location = window.location.pathname.split('/'),
          path = this.data.path = location[location.length - 1],
          self = this;

      if (this.data.blankModel.target_roles.length >= 1) {
        var default_role = this.data.blankModel.target_roles[0].name,
            default_role_type = this.data.blankModel.target_roles[0].type;
        this.data.blankModel.role = default_role;
        this.data.blankModel.target_role_type = default_role_type;
        this.data.blankModel.steps[0][0].role = default_role;
        this.data.blankModel.steps[0][0].target_role_type = default_role_type;
      }

      Handlebars.registerPartial('plan-step', $('#plan-step-template').html());
      Handlebars.registerPartial('plan-notification', $('#plan-notification-template').html());
      Handlebars.registerPartial('plan-tracking-notification', this.data.trackingTemplateSource);
      Handlebars.registerPartial('variables', this.data.variablesTemplateSource);
      this.getModes().done(function(){
        self.getPlan(path).done(function(){
          self.events();
          iris.versionTour.init();
          iris.typeahead.init();
        })
      });
      this.drag.init();
    },
    getModes: function(){
      var self = this;
      return $.getJSON(this.data.modesUrl, function(response){
        self.data.blankTrackingTemplateModel.modes = response;
        self.data.blankModel.modes = response;
      });
    },
    events: function(){
      var data = this.data;
      data.$page.on('click', data.addNotificationBtn, this.addNotification.bind(this));
      data.$page.on('click', data.removeNotificationBtn, this.removeNotification);
      data.$page.on('click', data.removeStepBtn, this.removeStep);
      data.$page.on('click', data.removeTrackingTemplateBtn, this.removeTrackingTemplate);
      data.$page.on('click', data.addStepBtn, this.addStep.bind(this));
      data.$page.on('click', data.addTrackingTemplateBtn, this.addTrackingTemplate.bind(this));
      data.$page.on('click', data.addTrackingTemplateBtn, this.updateNotificationFields.bind(this));
      $(data.createPlanBtn).on('click', this.createPlan.bind(this));
      data.$page.on('click', data.clonePlanBtn, this.clonePlan.bind(this));
      data.$page.on('click', data.clonePlanBtn, this.updateNotificationFields.bind(this));
      $(data.testPlanBtn).on('click', this.testPlan.bind(this));
      $(data.deletePlanBtn).on('click', this.deletePlan.bind(this));
      data.$page.on('click', data.showTestPlanModalBtn, this.testPlanModal.bind(this));
      data.$page.on('change', data.planNotificationInputs, this.updateValues);
      data.$page.on('click', data.aggregationBtn, this.toggleAggregation);
      data.$page.on('click', data.trackingTemplateBtn, this.toggleTrackingTemplate);
      data.$page.on('click', data.activatePlan, this.activatePlan.bind(this));
      data.$page.on('change', data.versionSelect, this.loadVersion.bind(this));
      data.$page.on('change', data.trackingType, this.updateTrackingPlaceholder.bind(this));
      data.$page.on('change', data.trackingType, this.updateNotificationFields.bind(this));
      data.$page.on('change', data.appSelect, this.renderVariables.bind(this));
      data.$page.on('change', data.testPlanInputs, this.updateTestPlanValues);
      data.$page.on('change', data.toggleDynamic, this.toggleDynamicTargets);
      data.$page.on('change', data.waitInput, this.updateStepTimes.bind(this))
      data.$page.on('change', data.countInput, this.updateStepTimes.bind(this))
      window.onbeforeunload = iris.unloadDialog.bind(this);
    },
    updateStepTimes: function() {
      var self = this;
      $('.step-time').each(function(_, element) {
        self.updateStepTime(element)
      });
    },
    updateStepTime: function(element) {
      var $element = $(element),
          waits = [],
          stepTime;

      $element.parent().siblings('.plan-notification').each(function(_, n) {
        var $n = $(n);
        if ($n.attr('data-mode') === 'view') {
          waits.push($n.children('.notification-wait')[0].title * $n.children('.notification-count')[0].title);
        } else {
          waits.push($n.find('.notification-wait')[0].value * $n.find('.notification-count')[0].value);
        }
      })
      stepTime = Math.min.apply(null, waits);
      if (stepTime === 0) {
        stepTime = 1;
      }
      $element.text(stepTime);
    },
    getPlan: function(plan){
      var self = this,
          template = this.data.template = Handlebars.compile(this.data.pageTemplateSource);

        //create list of templates available for plans.
        for (var i = 0, item; i < window.appData.templates.length; i++) {
          item = window.appData.templates[i];
          if (item.active){
            self.data.blankModel.availableTemplates.push(item.name);
          }
        }
        self.data.blankModel.availableTemplates.sort(function(a,b){
          a = a.toLowerCase();
          b = b.toLowerCase();

          if (a < b) {
            return -1;
          } else if (a > b) {
            return 1;
          } else {
            return 0;
          }
        });

        // if path is new, render in edit mode.
        if (plan === 'new') {
          self.data.$page.html(template(self.data.blankModel));
          iris.changeTitle('New Plan');
          return $.Deferred().resolve();
        } else {
          self.data.viewMode = true;
          return $.getJSON(this.data.url + plan).done(function(response){
            var max_idx = -1;
            self.data.id = response.id;
            self.data.name = response.name;
            self.data.ajaxResponse = response; //set response in root object for clone plan functionality.
            response.viewMode = self.data.viewMode;
            response.availableTemplates = self.data.blankModel.availableTemplates;
            // convert 'repeat' field to 'count' for frontend
            for (var i = 0; i < response.steps.length; i++) {
              for (var j = 0; j < response.steps[i].length; j++) {
                response.steps[i][j].count = response.steps[i][j].repeat + 1;
                if (response.steps[i][j].dynamic_index !== null) {
                  max_idx = Math.max(max_idx, response.steps[i][j].dynamic_index);
                }
                response.steps[i][j].dynamic = response.steps[i][j].dynamic_index !== null;
              }
            }
            response.max_dynamic_index = max_idx + 1;
            response.dynamic = max_idx !== -1;
            response.target_roles = window.appData.target_roles;
            response.target_role_type =  window.appData.target_roles[0].type;
            response.modes =  self.data.blankTrackingTemplateModel.modes;
            self.data.$page.html(template(response));
            self.loadVersionSelect();
            iris.changeTitle('Plan ' + response.name);
            self.updateStepTimes()
          }).fail(function(){
            iris.createAlert('"' + plan +'" plan not found. <a href="/plans/new">Create a new plan.</a>');
          });
        }
    },
    toggleAggregation: function(){
      $(this).parents('#aggregation').toggleClass('active');
    },
    toggleTrackingTemplate: function(){
      $('#tracking-notification').toggleClass('active');
    },
    toggleDynamicTargets: function(){
      var $toggle = $(this),
          dynamic = $toggle.prop('checked') ? '1' : '0';

      $('.plan-notification').each(function(){
        $(this).attr('data-dynamic', dynamic);
      });
    },
    clonePlan: function(){
      var response = this.data.ajaxResponse;
      response.viewMode = false;
      response.templates = window.appData.templates;
      response.priorities = window.appData.priorities;
      response.target_roles = window.appData.target_roles;
      response.applications = window.appData.applications;
      this.data.$page.html(this.data.template(response));
      this.updateStepTimes();
      iris.typeahead.init();
    },
    testPlanModal: function() {
      var
          $modal = $('#test-plan-modal'),
          $applicationSelect = $modal.find('#test-plan-modal-application-select'),
          frag = '';
      window.appData.applications.forEach(function(app) {
        frag += ['<option>', app['name'], '</option>'].join('');
      });
      $applicationSelect.html(frag);
      $modal.modal();
    },
    testPlan: function() {
      var
          $modal = $('#test-plan-modal'),
          $application = $modal.find('#test-plan-modal-application-select').val(),
          $context = JSON.parse(window.appData.applications.filter(function(l) {return l.name === $application})[0]['sample_context']) || {},
          targets = $modal.find('.test-plan-dynamic-target'),
          dynamic_targets = [],
          role,
          target;
      for (var i = 0; i < targets.length; i++) {
        role = $(targets[i]).find('select').val();
        target = $(targets[i]).find('input.tt-input').val();
        dynamic_targets.push({'role': role, 'target': target});
      }
      $.ajax({
          url: '/v0/incidents',
          data: JSON.stringify({
            application: $application,
            context: $context,
            dynamic_targets: dynamic_targets,
            plan: this.data.name
          }),
          method: 'POST',
          contentType: 'application/json'
      }).done(function(r) {
        window.location = '/incidents/' + r
      }).fail(function(r) {
        iris.createAlert('Failed creating test incident: ' + r.responseJSON['title'])
      }).always(function() {
        $modal.modal('hide');
      })
    },
    updateTestPlanValues: function(){
      var $this = $(this);

      if ($this.is('select[data-type="role"]')) {
        var $target = $this.parents('.test-plan-dynamic-target').find('input[data-typeaheadtype="target"]');
        $target.val('').attr(
            'placeholder',
            $this.find('option:selected').attr('data-url-type') + ' name');
        $target.attr('data-targettype', $this.find('option:selected').attr('data-url-type'));
        iris.typeahead.init();
      }

      $this.attr('value', $this.val());
    },
    deletePlan: function() {
      var $modal = $('#delete-plan-modal');
      $.ajax({
          url: '/v0/plans/' + this.data.id,
          method: 'DELETE'
      }).done(function() {
        window.onbeforeunload = null;
        window.location = '/plans/';
      }).fail(function(r) {
        iris.createAlert('Failed deleting plan: ' + r.responseJSON['title'])
      }).always(function() {
        $modal.modal('hide');
      })
    },
    loadVersionSelect: function(){
      var $select = $(this.data.versionSelect),
          self = this,
          frag = '';

      $.ajax({
        url: this.data.url,
        data: {
          name: this.data.name,
          fields: ['id', 'created', 'creator']
        },
        traditional: true
      }).done(function(r){
        r = r.reverse();
        for (var i = 0; i < r.length; i++) {
          var entry = r[i];
          frag += [
            '<option ', ((entry.id === self.data.id) ? 'selected' : ''),
            ' value="', entry.id,
            '" data-id="', entry.id + '">',
            'ID ', entry.id, ' - ',
            moment.unix(entry.created).local().format('YYYY/MM/DD HH:mm:ss [GMT]ZZ'),
            ' by ', entry.creator,
            ' </option>'
          ].join('');
        }
        $select.append(frag);
      });
    },
    loadVersion: function(e){
      var versionId = $(e.target).find('option:selected').attr('data-id'),
          self = this;
      this.getModes().done(function(){
        self.getPlan(versionId);
      });
      window.history.pushState(null, null, versionId); //update url bar for refreshes
    },
    activatePlan: function(e){
      var $el = $(e.target);
      $el.addClass('disabled');
      $.ajax({
          url: this.data.url + this.data.id,
          data: JSON.stringify({active: 1}),
          method: 'POST',
          contentType: 'application/json'
      }).done(function(){
        $el.attr('data-active', 1);
      }).fail(function(){
        iris.createAlert('Failed to activate.');
      }).always(function(){
        $el.removeClass('disabled');
      });
    },
    updateValues: function(){
      var $this = $(this);
      // Update selected attribute in the DOM on change. This is needed for
      // drag & drop to copy over attribute states.
      if ( $this.is('select') ) {
        $('option:selected', this).attr('selected',true).siblings().removeAttr('selected');
      }

      if ($this.is('select[data-type="role"]')) {
        $this.parents('.plan-notification').find('input[data-type="target"]').val('').attr(
            'placeholder',
            $this.find('option:selected').attr('data-url-type') + ' name');
        iris.typeahead.init();
      }

      $this.attr('value', $this.val());
    },
    addNotification: function(event){
      var $step = $(event.target).parents('.plan-step'),
          notifications = $('.plan-notification'),
          template = Handlebars.compile(this.data.notificationTemplateSource),
          max_id = 0,
          id,
          newModel;

      for (var i = 0; i < notifications.length; i++){
        id = notifications[i].id;
        // New notifications have ids like 'notification-n{{id}}'
        // Existing ones have ids like 'notification-{{id}}'
        if (id.startsWith('notification-n')) {
            max_id = Math.max(parseInt(id.slice(14)), max_id);
        }
      }
      // Create a new notification with id notification-n{{max_id + 1}}
      newModel = $.extend({},this.data.blankModel);
      newModel.id = 'n' + (max_id + 1).toString();
      newModel.dynamic = $('.toggle-dynamic').prop('checked');
      $step.find('.plan-notification-add').before(template(newModel));
      // re-init typeahead
      iris.typeahead.init();
    },
    removeNotification: function(){
      $(this).parents('.plan-notification').remove();
    },
    addStep: function(){
      var template = Handlebars.compile(this.data.stepTemplateSource);
      $(this.data.addStepBtn).before(template());
    },
    addTrackingTemplate: function(){
      var template = Handlebars.compile(this.data.trackingTemplateSource);
      $(this.data.addTrackingTemplateBtn).before(template(this.data.blankTrackingTemplateModel));
    },
    removeStep: function(){
      $(this).parents('.plan-step').remove();
    },
    removeTrackingTemplate: function(){
      $(this).parents('.tracking-template-step').remove();
    },
    updateSubmitModel: function(){
      // gets & checks data from plan inputs and prepares model for post.
      var model = this.data.submitModel,
          missingFields = [],
          $trackingEl = $('#tracking-notification.active'),
          planLength = 0;

      model.creator = window.appData.user;
      model.name = $('#plan-name').val();
      model.description = $('#plan-desc').val();
      model.threshold_window = parseFloat($('#threshold-window').val()) * 60;
      model.threshold_count = parseFloat($('#threshold-count').val());
      model.aggregation_window = parseFloat($('#aggregation-window').val()) * 60;
      model.aggregation_reset = parseFloat($('#aggregation-reset').val()) * 60;
      model.steps = [];
      model.isValid = true;

      // reset invalid inputs from previous check
      this.data.$page.find('.invalid-input').removeClass('invalid-input');
      this.data.$page.find('.alert-danger').remove();

      // validate model name
      if (!model.name) {
        $('#plan-name').addClass('invalid-input');
        //iris.createAlert('Missing fields: Plan name', 'danger', $('.plan-details') );
        missingFields.push('Plan name');
        model.isValid = false;
      }

      // validate plan notifications exist.
      if ($('.plan-notification').length === 0) {
        missingFields.push('steps/notifications');
        model.isValid = false;
      }

      // validate maximum plan duration
      $('.step-time').each(function(_, element) {
        planLength += parseInt($(element).html());
      });
      if ( planLength > 1440 ){
        iris.createAlert('Maximum plan duration exceeded: plan steps must add up to < 24 hours', 'danger', $('.plan-details') );
        model.isValid = false;
      }

      // collect data for notifications
      $('.plan-step:has(.plan-notification)').each(function(){
        var step = [],
            $this = $(this);

        $this.find('.plan-notification').each(function(){
          var notification = {};

          $(this).find('input:not(".tt-hint"):visible:not(".toggle-dynamic"),select:visible,textarea').each(function(){
            var $current = $(this),
                type = $current.attr('data-type'),
                val = $current.val();

            if (!val || !$current.get(0).checkValidity()) {
              $current.addClass('invalid-input');
              //iris.createAlert('Missing fields: ' + type, 'danger', $('.plan-details') );
              missingFields.push(type);
              model.isValid = false;
            }
            val = isNaN(val) ? val : parseFloat(val);
            // convert minutes to seconds for API
            if (type === 'wait') {
              val = Math.round(val * 60);
            }
            // convert count to repeat for API
            else if (type === 'count') {
              notification['repeat'] = val - 1;
            }
            notification[type] = val;
          });
          step.unshift(notification);
        });
        model.steps.push(step);
      });

      // collect data for tracking templates

      if ($trackingEl.length) {
        if ($trackingEl.find('.template-notification').length == 0) {
            return true;
        }

        model.tracking_type = $trackingEl.find('#tracking-type').val();
        model.tracking_key = $trackingEl.find('#tracking-key').val();

        if (!model.tracking_key) {
          $trackingEl.find('#tracking-key').addClass('invalid-input');
          missingFields.push('tracking target');
          model.isValid = false;
        }

        if (!model.tracking_type) {
          $trackingEl.find('#tracking-type').addClass('invalid-input');
          missingFields.push('tracking type');
          model.isValid = false;
        }

        if (model.tracking_type === 'slack' && (!model.tracking_key.startsWith('#') && !model.tracking_key.startsWith('@'))) {
          $trackingEl.find('#tracking-key').addClass('invalid-input');
          iris.createAlert('Invalid field for slack target: target must start with # for channels or @ for users', 'danger', $('.plan-details'));
          model.isValid = false;
        }

        if ($('.tracking-template-step').length === 0) {
          missingFields.push('tracking template');
          model.isValid = false;
        }

        model.tracking_template = {};
        $trackingEl.find('.tracking-template-step').each(function(){
          var $this = $(this),
              app = $this.find('.template-application').val(),
              template = {};

          if (!app) {
            $this.find('.template-application').addClass('invalid-input');
            missingFields.push();
            model.isValid = false;
          }

          $this.find('.template-notification:visible').each(function(){
            var $notification = $(this),
                type = $notification.attr('data-mode'),
                content = $notification.find('.notification-body').val();

            if (content) {
              template[type] = content;
            } else if ($notification.attr('data-required')) {
              $notification.find('input, textarea').addClass('invalid-input');
              missingFields.push(type);
              model.isValid = false;
            }
          });

          if (Object.keys(template).length === 0) {
            iris.createAlert('Empty tracking template for application: ' + app);
            model.isValid = false;
            $this.addClass('invalid-input');
          } else {
            model.tracking_template[app] = template;
          }

        });
      }

      if (missingFields.length > 0) {
        iris.createAlert('Missing fields: ' + missingFields.join(', '), 'danger', $('.plan-details'))
      }
    },
    createPlan: function(e){
      var model = this.data.submitModel,
          self = this,
          $button = $(e.target);
      $button.parents('.modal').modal('hide');
      this.updateSubmitModel();

      if (model && model.isValid) {
        $button.prop('disabled', true);
        $.ajax({
          url: self.data.url,
          data: JSON.stringify(model),
          method: 'POST',
          contentType: 'application/json'
        }).done(function(response){
          if (response) {
            window.onbeforeunload = null; //detach confirm dialog if plan is published.
            window.location = response;
          }
        }).fail(function(response){
          var errorTxt = (response && response.responseJSON && response.responseJSON.description) ? response.responseJSON.title + ' - ' + response.responseJSON.description : 'Plan creation failed.';
          $button.prop('disabled', false);
          iris.createAlert('Error: ' + errorTxt);
        });
      }
    },
    updateTrackingPlaceholder: function(e){
      var $type = $(e.target),
          $key = $(this.data.trackingKey);

      if ($type.val() === 'email') {
        $key.attr('placeholder', 'example@example.com');
      } else {
        $key.attr('placeholder', 'example');
      }
    },
    updateNotificationFields: function(e){
      var $type = $(this.data.trackingType).find(":selected").text();

      if ($type === 'email') {
        $(".template-notification[data-mode='email_subject']").show();
        $(".template-notification[data-mode='email_text']").show();
        $(".template-notification[data-mode='email_html']").show();
        $(".template-notification[data-mode='body']").hide().val("");
      } else {
        $(".template-notification[data-mode='email_subject']").hide().val("");
        $(".template-notification[data-mode='email_text']").hide().val("");
        $(".template-notification[data-mode='email_html']").hide().val("");
        $(".template-notification[data-mode='body']").show();
      };
    },
    drag: {
      data: {
        $draggedEl: null
      },
      init: function(){
        var self = this,
            $planDetails = $('.plan-details');

        $planDetails.on('dragstart','.plan-notification[data-mode="edit"]', self.handleDragStart.bind(this));
        $planDetails.on('dragend','.plan-notification[data-mode="edit"]', self.handleDragEnd.bind(this));
        $planDetails.on('dragover','.plan-step[data-mode="edit"]', self.handleDragOver);
        $planDetails.on('dragenter','.plan-step[data-mode="edit"]', self.handleDragEnter);
        $planDetails.on('dragleave','.plan-step[data-mode="edit"]', self.handleDragLeave);
        $planDetails.on('drop', '.plan-step[data-mode="edit"]', self.handleDrop);
        $planDetails.on('dragstart', '.plan-step[data-mode="edit"]', self.handleStepStart.bind(this));

        //Allow text highlighting
        //Fix for HTML5 drag and drop - removes drag attribute on input focus and re-adds it on blur

        $planDetails.on('focus','.plan-notification[data-mode="edit"] input', function(){
          $(this).parents('.plan-notification, .plan-step').attr('draggable', false);
        });

        $planDetails.on('blur','.plan-notification[data-mode="edit"] input', function(){
          $(this).parents('.plan-notification, .plan-step').attr('draggable', true);
        });
      },
      handleStepStart: function(e){
        e = e.originalEvent;
        if (!$(e.target).hasClass('plan-notification')) {
          iris.typeahead.destroy();
          this.data.$draggedEl = $(e.target);
          e.dataTransfer.effectAllowed = "move";
          e.dataTransfer.dropEffect = "move";
          e.dataTransfer.setData('text/html', e.target.innerHTML);
        }
      },
      handleDragStart: function(e){
        e = e.originalEvent;
        e.stopPropagation();
        this.data.$draggedEl = $(e.target);
        iris.typeahead.destroy();
        $(e.target).addClass('dragging').parents('.plan-step').addClass('drag-source');
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData('text/html', e.target.outerHTML);
      },
      handleDragEnd: function(e){
        typeahead.init();
        $(e.target).removeClass('dragging');
        $('.drag-source').removeClass('drag-source');
      },
      handleDragOver: function(e){
        $(this).addClass('drag-over');
        e.preventDefault();
        return false;
      },
      handleDragEnter: function(e){
        e.preventDefault();
        $(this).addClass('drag-over');
      },
      handleDragLeave: function(e){
        e.preventDefault();
        $(this).removeClass('drag-over');
      },
      handleDrop: function(e){
          var parent = iris.plan,
            self = parent.drag,
            $this = $(this);
        e.preventDefault();
        e = e.originalEvent;

        if(!$this.hasClass('drag-source')) {

          //if dropped item is a step, switch steps, else move notification
          if(self.data.$draggedEl && self.data.$draggedEl.hasClass('plan-step')){
            var temp = $this.html();
            $this.html(e.dataTransfer.getData('text/html'));
            self.data.$draggedEl.html(temp);
            iris.typeahead.init();
          } else {
            $this.prepend(e.dataTransfer.getData('text/html'));
            self.data.$draggedEl.remove();
            iris.typeahead.init();
          }
        }
        $('.drag-over').removeClass('drag-over');
        $('.dragging').removeClass('dragging');
        $('.drag-source').removeClass('drag-source');
      }
    },
    getVariablesForApp: function(app){
      var apps = window.appData.applications;
      // get variables for apps in current template application
      for (var i = 0; i < apps.length; i++){
        if (apps[i].name === app) {
          var variables = {};
          for (var j = 0; j < apps[i].variables.length; j++){
            variables[apps[i].variables[j]] = {
              'required': apps[i].required_variables.indexOf(apps[i].variables[j]) !== -1
            };
          }
          return variables;
        }
      }
    },
    renderVariables: function(e){
      var $el = $(e.target),
          app = $el.val(),
          template = Handlebars.compile(this.data.variablesTemplateSource);
      $el.parents().find('.variables').html(template({variables: this.getVariablesForApp(app)}));
    }
  }, //end iris.plan
  templates: {
    initialized: false,
    data: {
      url: '/v0/templates',
      $page: $('.main'),
      $table: $('#templates-table'),
      $filterForm: $('#filter-form'),
      tableTemplate: $('#templates-table-template').html(),
      DataTable: null,
      dataTableOpts: {
        orderClasses: false,
        order: [[2, 'desc']]
      }
    },
    init: function(){
      iris.changeTitle('Templates');
      if (this.initialized == false) {
        this.initFilters();
        this.events();
        this.initialized = true;
      }
      iris.tables.filterTable.call(this);
    },
    events: function(){
      var data = this.data,
          $table = data.$table;

      $table.on('click', 'tbody tr[data-route]', function(e){
        if (e.target.tagName !== 'A') {
          if ((e.ctrlKey || e.metaKey)) {
            window.open('/templates/' + $(this).attr('data-route'));
          } else {
            window.location = '/templates/' + $(this).attr('data-route');
          }
        }
      });
      data.$filterForm.on('submit', iris.tables.filterTable.bind(this));
    },
    getData: function(params){
      return $.getJSON(this.data.url, params).fail(function(){
        iris.createAlert('No templates found');
      });
    },
    initFilters: function(){
      iris.typeahead.init('user');
      $('.datetimepicker').datetimepicker({
        showClose: true,
        keyBinds: {'delete': null}
      });
    }
  }, //end iris.templates
  template: {
    data: {
      url: '/v0/templates/',
      name: '',
      id: null,
      path: null,
      $page: $('.main'),
      createTemplateBtn: '#publish-template',
      cloneTemplateBtn: '#clone-template',
      addStepBtn: '#add-step',
      removeStepBtn: '.remove-step',
      templateSteps: '.template-steps',
      appSelect: '.template-application',
      versionSelect: '.version-select',
      activateTemplate: '.badge[data-active="0"]',
      previewTemplate: '.preview-template',
      viewRelated: '.view-related',
      relatedPlans: [],
      stepTemplateSource: $('#template-step-template').html(),
      variablesTemplateSource: $('#variables-template').html(),
      templateSource: $('#template-template').html(),
      template: null,
      submitModel: {},
      modes: window.appData.modes,
      user: window.appData.user,
      blankModel: {
        applications: window.appData.applications,
        modes: window.appData.modes,
        content: {
          application: {}
        },
        viewMode: false,
        creator: window.appData.user
      }
    },
    init: function(){
      var location = window.location.pathname.split('/'),
          path = this.data.path = location[location.length - 1],
          self = this;

      for (var i = 0; i < window.appData.modes.length; i++) {
          this.data.blankModel.content.application[window.appData.modes[i]] = {
              body: "",
              subject: ""
          };
      }

      Handlebars.registerPartial('template-step', $('#template-step-template').html());
      Handlebars.registerPartial('template-notification', $('#template-notification-template').html());
      Handlebars.registerPartial('variables', this.data.variablesTemplateSource);
      this.getTemplate(path).done(function(){
        self.events();
        iris.versionTour.init();
      });
    },
    events: function(){
      var data = this.data;
      $(data.createTemplateBtn).on('click', this.createTemplate.bind(this));
      data.$page.on('click', data.cloneTemplateBtn, this.cloneTemplate.bind(this));
      data.$page.on('click', data.addStepBtn, this.addStep.bind(this));
      data.$page.on('click', data.removeStepBtn, this.removeStep);
      data.$page.on('click', data.previewTemplate, this.previewTemplate);
      data.$page.on('click', data.activateTemplate, this.activateTemplate.bind(this));
      data.$page.on('click', data.viewRelated, this.viewRelated.bind(this));
      data.$page.on('change', data.appSelect, this.renderVariables.bind(this));
      data.$page.on('change', data.versionSelect, this.loadVersion.bind(this));
      window.onbeforeunload = iris.unloadDialog.bind(this);
    },
    addStep: function(){
      var template = Handlebars.compile(this.data.stepTemplateSource);
      $(this.data.addStepBtn).before(template(this.data.blankModel));
    },
    removeStep: function(){
      $(this).parents('.step').remove();
    },
    getTemplate: function(path){
      var self = this,
          template = this.data.template = Handlebars.compile(this.data.templateSource);

        //if path is new, render in edit mode.
        if (path === 'new') {
          var response = self.data.blankModel;
          response.viewMode = false;
          for (var i = 0, keys = Object.keys(response.content); i < keys.length; i++) {
            response.content[keys[i]].variables = self.getVariablesForApp(keys[i]);
          }
          self.data.$page.html(template(self.data.blankModel));
          iris.changeTitle('Edit Template');
          return $.Deferred().resolve();
        } else {
          self.data.viewMode = true;
          return $.getJSON(this.data.url + path).done(function(response){
            //shim response data for handlebars
            response.viewMode = true;
            response.applications = window.appData.applications;
            response.modes = window.appData.modes;
            for (var i = 0, keys = Object.keys(response.content); i < keys.length; i++) {
              response.content[keys[i]].application = keys[i];
              response.content[keys[i]].variables = self.getVariablesForApp(keys[i]);
              for (var j = 0; j < window.appData.modes.length; j++) {
                if (!(window.appData.modes[j] in response.content[keys[i]])) {
                  response.content[keys[i]][window.appData.modes[j]] = {
                    body: "",
                    subject: ""
                  };
                }
              }
            }
            self.data.ajaxResponse = response; //set response in root object for clone path functionality.
            self.data.id = response.id;
            self.data.name = response.name;
            self.data.relatedPlans = response.plans;
            self.data.$page.html(template(response));
            self.loadVersionSelect();
            iris.changeTitle('Template ' + self.data.name);
          }).fail(function(){
            iris.createAlert('"' + path +'" template not found. <a href="/templates/new">Create a new template.</a>');
          });
        }
    },
    getVariablesForApp: function(app){
      var apps = window.appData.applications;
      // get variables for apps in current template application
      for (var i = 0; i < apps.length; i++){
        if (apps[i].name === app) {
          var variables = {};
          for (var j = 0; j < apps[i].variables.length; j++){
            variables[apps[i].variables[j]] = {
              'required': apps[i].required_variables.indexOf(apps[i].variables[j]) !== -1
            };
          }
          return variables;
        }
      }
    },
    renderVariables: function(e){
      var $el = $(e.target),
          app = $el.val(),
          self = this,
          template = Handlebars.compile(self.data.variablesTemplateSource);

      self.data.$page.find(self.data.previewTemplate).css('display', !app ? 'none' : '');
      $el.parents('.step').find('.variables').html(template({variables: this.getVariablesForApp(app)}));
    },
    cloneTemplate: function(){
      var response = this.data.ajaxResponse;
      response.viewMode = false;
      this.data.$page.html(this.data.template(response));
    },
    loadVersionSelect: function(){
      var $select = $(this.data.versionSelect),
          self = this,
          frag = '';

      $.ajax({
        url: this.data.url,
        data: {
          name:this.data.name,
          fields: ['id', 'created', 'creator']
        },
        traditional: true
      }).done(function(r){
        r = r.reverse();
        for (var i = 0; i < r.length; i++) {
          var entry = r[i];
          frag += [
            '<option ', ((entry.id === self.data.id) ? 'selected' : ''),
            ' value="', entry.id,
            '" data-id="', entry.id + '">',
            'ID ', entry.id, ' - ',
            moment.unix(entry.created).local().format('YYYY/MM/DD HH:mm:ss [GMT]ZZ'),
            ' by ', entry.creator,
            ' </option>'
          ].join('');
        }
        $select.append(frag);
      });
    },
    loadVersion: function(e){
      var versionId = $(e.target).find('option:selected').attr('data-id');
      this.getTemplate(versionId);
      window.history.pushState(null, null, versionId); //update url bar for refreshes
    },
    activateTemplate: function(e){
      var $el = $(e.target);

      $.ajax({
          url: this.data.url + this.data.id,
          data: JSON.stringify({active: 1}),
          method: 'POST',
          contentType: 'application/json'
      }).done(function(){
        $el.attr('data-active', 1);
      }).fail(function(){
        iris.createAlert('Failed to activate.');
      });
    },
    viewRelated: function(e){
      var $modal = $($(e.target).attr('data-target')),
          frag = '',
          data = this.data.relatedPlans;
      if (data.length) {
        for (var i = 0; i < data.length; i++) {
          frag += '<li class="border-bottom"><a href="/plans/' + data[i]["id"] + '">' + data[i]["name"] + ' - ID ' + data[i]['id']+ '</a></li>';
        }
        $modal.find('.modal-body .modal-list').html(frag);
      } else {
        $modal.find('.modal-body .modal-list').text('No plans are currently using this template.');
      }
    },
    updateSubmitModel: function(){
      // gets & checks data from plan inputs and prepares model for post.
      var model = this.data.submitModel,
          $steps = $(this.data.templateSteps),
          self = this;

      model.creator = this.data.user;
      model.name = $('#template-name').val();
      model.content = {};
      $steps.find('.step').each(function(){
        var $this = $(this),
            application = $this.find('.template-application').val();

        model.content[application] = {};

        $this.find('.template-notification').each(function(){
          var mode = $(this).attr('data-mode');

          if (mode === 'email') {
            model.content[application][mode] = {
              subject: $(this).find('.template-subject').val(),
              body: $(this).find('.template-body').val()
            }
          } else {
            model.content[application][mode] = {
              subject: '',
              body: $(this).find('.template-body').val()
            }
          }
        });
      });

      // reset invalid inputs from previous check
      this.data.$page.find('.invalid-input').removeClass('invalid-input');
      if (
        $('.view-template select, .view-template input, .view-template textarea')
        .filter(function(){
          return !$(this).val();
        })
        .addClass('invalid-input')
        .length > 0
      ){
        model.isValid = false;
        iris.createAlert('Missing fields', 'danger', this.data.$page);
      } else if($steps.find('.step').length > 1){
        var apps = [];
        model.isValid = true;
        $steps.find('.template-application').each(function(){
          var val = $(this).val();
          if (apps.indexOf(val) !== -1) {
            $(this).addClass('invalid-input');
            model.isValid = false;
            iris.createAlert('Please pick a unique application for each template.', 'danger', self.data.$page);
          } else {
            apps.push(val);
          }
        });
      } else {
        model.isValid = true;
      }
    },
    previewTemplate: function(){
      var $this = $(this),
          mode = $this.attr('data-mode'),
          $notification = $this.parents('.template-notification'),
          $step = $this.parents('.step'),
          submitModel = {},
          $modal = $('#preview-template-modal'),
          $modalBody = $modal.find('.modal-body');

      submitModel.application = $step.find('.template-application').val();
      if (!submitModel.application) {
          iris.createAlert('Please select an application.', 'danger', $modalBody);
          return;
      }
      submitModel.templateSubject = $notification.find('.template-subject').val() || ' ';
      submitModel.templateBody = $notification.find('.template-body').val();

      $modalBody.html('<i class="loader"></i>');
      $.ajax({
        type: 'post',
        url: '/validate/jinja',
        dataType: 'json',
        data: submitModel
      }).done(function(r){
        if (r.template_subject || r.template_body) {
          $modalBody.html( ( (mode === 'email') ? '<div class="preview-subject">' + Handlebars.helpers.breakLines(r.template_subject) + '</div>' : '') + '<div class="preview-body">' + Handlebars.helpers.breakLines(r.template_body) + '</div>');
        } else {
          $modalBody.empty();
          iris.createAlert('Invalid template', 'danger', $modalBody);
        }
      }).fail(function(r){
        $modalBody.empty();
        if (r.responseJSON && r.responseJSON.lineno && r.responseJSON.error) {
          iris.createAlert('Line: ' + r.responseJSON.lineno + '<br />Error: ' + r.responseJSON.error, 'danger', $modalBody);
        } else if (r.responseJSON && r.responseJSON.error) {
          iris.createAlert('Error: ' + r.responseJSON.error, 'danger', $modalBody);
        } else {
          iris.createAlert('Invalid template', 'danger', $modalBody);
        }
      });
    },
    createTemplate: function(e){
      var model = this.data.submitModel,
          self = this,
          $button = $(e.target);

      this.updateSubmitModel();

      if (model && model.isValid) {
        $button.prop('disabled', true);
        $.ajax({
          url: self.data.url,
          data: JSON.stringify(model),
          method: 'POST',
          contentType: 'application/json'
        }).done(function(response){
          if (response) {
            window.onbeforeunload = null; //detach confirm dialog if plan is published.
            window.location = response;
          }
        }).fail(function(response){
          var errorTxt = (response && response.responseJSON && response.responseJSON.error) ? response.responseJSON.error : 'Template creation failed.';
          $button.prop('disabled', false);
          iris.createAlert('Error: ' + errorTxt);
        });
      }
    }
  }, //end iris.template
  incidents: {
    initialized: false,
    data: {
      url: '/v0/incidents/',
      fields: ['id', 'owner', 'application', 'plan', 'plan_id', 'created', 'updated', 'active', 'current_step'],
      $page: $('.main'),
      $table: $('#incidents-table'),
      $filterApp: $('#filter-application'),
      $filterForm: $('#filter-form'),
      $claimModal: $('#claim-modal'),
      claimModalBtn: '#show-claim',
      claimBtn: '#claim-active-btn',
      tableTemplate: $('#incidents-table-template').html(),
      summaryCtxHash: {},
      incidentData: null,
      DataTable: null,
      dataTableOpts: {
        orderClasses: false,
        dom: '<"claim-container"><"pull-right"l>tip',
        order: [[0, 'desc']],
        oLanguage: {
          sEmptyTable: "Use the filters above to find incidents",
          sZeroRecords: "Use the filters above to find incidents"
        },
        columns: [
          null,
          null,
          { width: '25%', orderable: false },
          null,
          { width: '10%' },
          { width: '10%' },
          null,
          null
        ]
      }
    },
    init: function(){
      iris.changeTitle('Incidents');
      var self = this;
      if (this.initialized == false) {
        this.initFilters();
        this.events();
        this.initialized = true;
      }
      this.data.dataTableOpts.fnInitComplete = this.tableDrawComplete.bind(self);
      iris.tables.filterTable.call(this);
      this.data.$table.on('draw.dt', self.getSummary.bind(self));
    },
    tableDrawComplete: function() {
      var self = this,
          $empty = $('.dataTables_empty');
      if ($empty && $('#filter-active').prop('checked')) {
        $empty.append($('<br>'))
              .append($('<a>Try viewing all incidents instead of just active incidents</a>')
                        .click(function() {
                           $('#filter-all').prop('checked', 'true');
                           self.data.$filterForm.submit();
                        }));
      }
      $('div.claim-container').html('<button type="button" class="btn btn-default blue btn-sm" id="show-claim">Claim Active Incidents</button>');
    },
    events: function(){
      var data = this.data,
          $table = data.$table,
          self = this;

      $table.on('click', 'tbody tr[data-route]', function(e){
        if (e.target.tagName !== 'A') {
          if ((e.ctrlKey || e.metaKey)) {
            window.open('/incidents/' + $(this).attr('data-route'));
          } else {
            window.location = '/incidents/' + $(this).attr('data-route');
          }
        }
      });

      $table.on('click', '.claim-incident', function(e){
        e.stopPropagation();
        self.claimIncident(e);
      });
      data.$page.on('click', self.data.claimModalBtn, self.claimModal.bind(this));
      data.$claimModal.on('click', self.data.claimBtn, self.claimActive.bind(this));
      data.$filterForm.on('submit', iris.tables.filterTable.bind(this));
    },
    claimModal: function(){
      var actives = this.data.DataTable.rows(function(_, _, x) { return x.getAttribute('data-active') === '1' }),
          activeCount = actives.flatten().length;
      if (activeCount > 0) {
        $('#active-count').html(actives.flatten().length);
        this.data.$claimModal.modal();
      } else {
        iris.createAlert('No active incidents to claim');
      }
    },
    claimActive: function(){
      var self = this,
          actives = this.data.DataTable.rows(function(_, _, x) { return x.getAttribute('data-active') === '1' }),
          activeIds = [];
      activeIds = Array.from(actives.nodes().map(function(x) { return x.getAttribute('data-route') }));
       $.ajax({
        url: self.data.url + 'claim',
        data: JSON.stringify({
          owner: window.appData.user,
          incident_ids: activeIds
        }),
      method: 'POST',
      contentType: 'application/json'
      }).done(function(data) {
        iris.createAlert('Successfully claimed ' + data.claimed.length + ' incidents: ' + data.claimed.join(', '), 'success');
        self.init();
      }).fail(function() {
        iris.createAlert('Error: failed to claim incidents');
      }
      )
    },
    getData: function(params){
      //merge params and fields
      params['fields'] = this.data.fields;
      params['limit'] = iris.data.tableEntryLimit;

      return $.ajax({
        url: this.data.url,
        data: params,
        traditional: true
      }).fail(function(){
        iris.createAlert('No incidents found');
      });
    },
    getSummary: function(){
      var self = this,
          params = {
            'fields': ['id', 'context', 'application'],
            'id__in': null
          },
          templateSource = $('#summary-template').html(),
          getCtxRequest = new $.Deferred(),
          idList = [],
          $summaryTh = this.data.$table.find('td.summary');

      this.data.$table.find('tbody tr').each(function(){
        var id = $(this).data('route');
        if (id) {
          idList.push(id);
        }
      });

      if (idList.length) {
        var filteredIdList = idList.filter(function(i){ return self.data.summaryCtxHash[i] === undefined});

        if (filteredIdList.length) {
          params.id__in = filteredIdList.toString();
          $summaryTh.attr('data-loading', true);
          getCtxRequest = $.ajax({
            url: self.data.url,
            data: params,
            traditional: true
          }).done(function(data){
            for (var i = 0; i < data.length; i++) {
              var item = data[i];
              self.data.summaryCtxHash[item.id] = item;
            }
          });
        } else {
          getCtxRequest.resolve(); // resolve promise if all data exists in hash
        }

        getCtxRequest.done(function(){
          $summaryTh.attr('data-loading', '');
          for (var i = 0; i < idList.length; i++) {
            var item = self.data.summaryCtxHash[idList[i]],
                app = window.appData.applications.filter(function(l){ return l.name === item.application })[0],
                currTmplSrc,
                template;

            currTmplSrc = app && app.summary_template || templateSource;
            template = Handlebars.compile(currTmplSrc);
            self.data.$table.find('tr[data-route=' + item.id + '] .incident-summary').html(template(item));
          }
        });
      }

    },
    initFilters: function(){
      for (var i = 0; i < window.appData.applications.length; i++) {
        this.data.$filterApp.append($(document.createElement('option')).attr({ value: window.appData.applications[i].name }).text(window.appData.applications[i].name));
      }
      iris.typeahead.init('user');
      $('.datetimepicker').datetimepicker({
        showClose: true,
        keyBinds: {'delete': null}
      });
    },
    claimIncident: function(e){
      var $this = $(e.target),
          owner = $this.attr('data-action') === 'claim' ? window.appData.user : null,
          self = this,
          incidentId = $this.attr('data-id');
      $this.prop('disabled', true);
      $.ajax({
        url: self.data.url + incidentId,
        data: JSON.stringify({
          owner: owner
        }),
        method: 'POST',
        contentType: 'application/json'
      }).done(function(data){
        var active = data.active;
        incidentId = data.incident_id;
        var message = active ? 'Incident ' + incidentId + ' unclaimed.' : 'Incident ' + incidentId + ' claimed.';
        iris.createAlert(message, 'success', null, null, 'fixed');
        $this.attr('data-action', active ? 'claim' : 'unclaim')
          .text(active ? 'Claim Incident' : 'Unclaim Incident')
          .parents('tr[data-route=' + incidentId + ']')
          .attr('data-active', active ? 1 : 0)
          .find('.owner').text(active ? 'Unclaimed' : owner);
      }).fail(function(){
        iris.createAlert('Failed to modify incident', 'danger');
      }).always(function(){
        $this.prop('disabled', false);
      });
    }
  },
  incident: {
    data: {
      url: '/v0/incidents/',
      $page: $('.main'),
      id: null,
      incident: null,
      appPlanUrl: '/v0/applications/',
      planTypeahead: 'input.typeahead',
      showReescalateBtn: '#re-escalate-modal-btn',
      reescalateModal: '#re-escalate-modal',
      selectPlanBtn: '#re-escalate-plan-btn',
      reescalateBtn: '#re-escalate-btn',
      reescalatePlanContainer: '.re-escalate-plan-container',
      claimIncidentBtn: '#claim-incident',
      showAddCommentBtn: '#show-comment',
      hideAddCommentBtn: '#cancel-comment',
      addCommentBtn: '#comment-incident',
      addCommentContainer: '#add-comment',
      commentContainer: '.comment-list',
      commentSource: $('#comment-template').html(),
      incidentSource: $('#incident-template').html(),
      messageTable: '#incident-messages-table',
      DataTable: null,
      dataTableOpts: {
        orderClasses: false,
        order: [[0, 'desc']],
        oLanguage: {
          sEmptyTable: "No messages have been sent for this incident.",
          sZeroRecords: "No messages have been sent for this incident."
        }
      }
    },
    init: function(){
      var location = window.location.pathname.split('/'),
          path = this.data.id = location[location.length - 1],
          self = this;
      Handlebars.registerPartial('comment', this.data.commentSource);
      this.getIncident(path).done(function() {
        self.events();
      })
    },
    events: function(){
      var data = this.data;
      data.$page.on('click', data.claimIncidentBtn, this.claimIncident.bind(this));
      data.$page.on('click', data.showAddCommentBtn, this.showComment.bind(this));
      data.$page.on('click', data.hideAddCommentBtn, this.hideComment.bind(this));
      data.$page.on('click', data.addCommentBtn, this.addComment.bind(this));
      data.$page.on('click', data.showReescalateBtn, this.reescalateModal.bind(this));
      data.$page.on('click', data.selectPlanBtn, this.selectPlan.bind(this));
      data.$page.on('click', data.reescalateBtn, this.reescalateIncident.bind(this));
    },
    showComment: function() {
      $(this.data.addCommentContainer).show();
      $(this.data.showAddCommentBtn).hide();
      $('#comment-body').focus();
    },
    hideComment: function() {
      $('#comment-body').val('');
      $(this.data.addCommentContainer).hide();
      $(this.data.showAddCommentBtn).show();
    },
    addComment: function() {
      var self = this,
          commentContainer = $(self.data.addCommentContainer),
          comment = {
            author: window.appData.user,
            content: $('#comment-body').val()
          };
      if (comment.content === '') {
        iris.createAlert('Error: Empty comment body', 'danger', commentContainer)
      } else {
        $.ajax({
          url: self.data.url + self.data.id + '/comments',
          data: JSON.stringify(comment),
          method: 'POST',
          contentType: 'application/json'
        }).done(function() {
          var template = Handlebars.compile(self.data.commentSource);
          comment['created'] = Date.now() / 1000;
          $(self.data.commentContainer).append(template(comment));
          $('.no-comments').hide();
          self.hideComment();
        }).fail(function(){
          iris.createAlert('Failed to post comment', 'danger', commentContainer)
        })
      }
    },
    getIncident: function(path){
      var self = this;

      return $.getJSON(self.data.url + path).done(function(response){
        self.data.incident = response;
        iris.changeTitle('Incident #' + response.id);
        $.getJSON('/v0/applications/' + response.application).done(function(application){
          if (application.context_template) {
            Handlebars.registerPartial('context_template', application.context_template);
          }
          var template = self.data.template = Handlebars.compile(self.data.incidentSource);
          response.user = window.appData.user;
          self.data.$page.html(template(response));
          self.data.DataTable = $(self.data.messageTable).DataTable(self.data.dataTableOpts);
          iris.tables.bindArrowKeys(self.data.DataTable);
        });
      }).fail(function(){
        iris.createAlert('Incident not found');
      });
    },
    claimIncident: function(e){
      var $this = $(e.target),
          owner = $this.attr('data-action') === 'claim' ? window.appData.user : null,
          self = this,
          incidentId = $this.attr('data-id');
      $this.prop('disabled', true);
      $.ajax({
        url: self.data.url + incidentId,
        data: JSON.stringify({
          owner: owner
        }),
        method: 'POST',
        contentType: 'application/json'
      }).done(function(){
        self.getIncident(incidentId).done(function(){
          var message = owner ? 'Incident ' + incidentId + ' claimed.' : 'Incident ' + incidentId + ' unclaimed.';
          iris.createAlert(message, 'success');
        });
      }).fail(function(){
        iris.createAlert('Failed to modify incident', 'danger');
      }).always(function(){
        $this.prop('disabled', false);
      });
    },
    reescalateModal: function() {
      var $modal = $(this.data.reescalateModal),
          self = this;
          $field = $(self.data.planTypeahead);
      $field.typeahead('destroy').each(function(){
        var $this = $(this),
            remoteUrl = self.data.appPlanUrl + self.data.incident.application + '/plans?name__contains=%QUERY';
            results = new Bloodhound({
              datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
              queryTokenizer: Bloodhound.tokenizers.whitespace,
              remote: {
                url: remoteUrl,
                wildcard: '%QUERY',
              }
            });
        $this.typeahead(null, {
          hint: true,
          async: true,
          highlight: true,
          display: 'name',
          source: results,
        }).on('typeahead:select', function(e, plan){
          $this.attr('value', plan.name);
          self.previewPlan(plan);
        }).on('input', function(e) {
          $this.attr('value', e.target.value);
        });
      });
      $modal.modal();
    },
    // Extra button to select re-escalation plan if plan name is typed fully
    selectPlan: function() {
      var planName = $('#re-escalate-typeahead').attr('value'),
          self = this;

      self.resetPlanPreview();
      // Get plan details from name
      $.ajax({
        url: '/v0/plans',
        data: {name: planName, active: 1},
        method: 'GET',
        contentType: 'application/json'
      }).done(function(r) {
        if (!r.length) {
          iris.createAlert('No plan found for query: ' + planName, 'danger', $('.modal-body'));
        } else {
          self.previewPlan(r[0]);
        }
      }).fail(function() {
        iris.createAlert('No plan found for query: ' + planName, 'danger', $('.modal-body'));
      })
    },
    resetPlanPreview: function() {
      $(this.data.reescalateBtn).prop('disabled', true);
      $(this.data.reescalatePlanContainer).html('');
    },
    previewPlan: function(plan) {
      var planContainer = $(this.data.reescalatePlanContainer),
          planTemplate = Handlebars.compile($('#re-escalation-plan-template').html())
          self = this;
      // Get plan steps to preview re-escalation plan
      $.ajax({
        url: '/v0/plans/' + plan.id,
        method: 'GET',
      }).done(function(r) {
        // Dynamic plans will have steps that define dynamic_index
        // These can't be used for re-escalation
        dynamic = r.steps.some(function(step){
          return step.some(function(notification){
            return notification.dynamic_index != undefined })
          });
        if (dynamic) {
          self.resetPlanPreview();
          iris.createAlert('Cannot re-escalate with dynamic plan: ' + plan.name, 'danger', $('.modal-body'))
        } else {
          iris.dismissAlerts();
          planContainer.html(planTemplate(r));
          $(self.data.reescalateBtn).prop('disabled', false);
        }
      }).fail(function(r) {
        self.resetPlanPreview();
        iris.createAlert('Failed to fetch plan details', 'danger', $('.modal-body'))
      })
    },
    /* Re-ecalate an incident. This triggers the following actions:
       1. Claim the incident if it is unclaimed
       2. Re-raise the incident with the specified escalation plan
       3. Comment on the original incident with a link to the new incident
       4. Comment on the new incident with a link to the original
       5. Navigate to the new incident page
    */
    reescalateIncident: function() {
      var self = this,
          $modal = $('.modal-body'),
          plan = $('#re-escalate-typeahead').attr('value'),
          claim;
      // Claim incident if necessary
      if (self.data.incident.active) {
        claim = $.ajax({
          url: self.data.url + self.data.incident.id,
          data: JSON.stringify({
            owner: window.appData.user
          }),
          method: 'POST',
          contentType: 'application/json'
        }).fail(function() {
          iris.createAlert('Failed to claim original incident', 'danger', $modal);
        })
      } else {
        claim = $.Deferred().resolve();
      }
      // Then, create a new incident
      claim.then(function() {
        return $.ajax({
          url: '/v0/incidents',
          data: JSON.stringify({
            application: self.data.incident.application,
            context: self.data.incident.context,
            plan: plan
          }),
          method: 'POST',
          contentType: 'application/json'
        }).fail(function(){
          iris.createAlert('Failed creating re-escalation incident', 'danger', $modal);
        })
      // Finally, post comments to new and original incidents
      }).then(function(reescalateId){
        var author = window.appData.user;
        var comment = {
          author: window.appData.user,
          content: 'Incident re-escalated as [incident ' + reescalateId + '](/incidents/'
            + reescalateId + ') by ' + author
        }
        var reescalationComment = {
          author: window.appData.user,
          content: 'Incident re-escalated from [incident ' + self.data.id + '](/incidents/'
          + self.data.id + ') by ' + author
        }
        $.when(
          $.ajax({
            url: self.data.url + self.data.id + '/comments',
            data: JSON.stringify(comment),
            method: 'POST',
            contentType: 'application/json'
          }),
          $.ajax({
            url: self.data.url + reescalateId + '/comments',
            data: JSON.stringify(reescalationComment),
            method: 'POST',
            contentType: 'application/json'
          })
        ).done(function() {
          window.location = '/incidents/' + reescalateId;
        }).fail(function(){
          iris.createAlert('Failed to post re-escalation comments for re-escalation incident ' + reescalateId,
            'danger', $modal);
        })
      })
    }
  },
  messages: {
    initialized: false,
    data: {
      url: '/v0/messages',
      fields: ['id', 'batch', 'target', 'subject', 'incident_id', 'priority', 'application', 'mode', 'sent', 'mode_changed', 'target_changed'],
      $page: $('.main'),
      $table: $('#messages-table'),
      $filterApp: $('#filter-application'),
      $filterPriority: $('#filter-priority'),
      $filterForm: $('#filter-form'),
      tableTemplate: $('#messages-table-template').html(),
      DataTable: null,
      dataTableOpts: {
        orderClasses: false,
        order: [[0, 'desc']],
        oLanguage: {
          sEmptyTable: "Use the filters above to find messages",
          sZeroRecords: "Use the filters above to find messages"
        },
        columns: [
          null,
          null,
          null,
          { width: '30%' },
          null,
          null,
          null,
          null,
          null
        ]
      }
    },
    init: function(){
      iris.changeTitle('Messages');
      if (this.initialized == false) {
        this.initFilters();
        this.events();
        this.initialized = true;
      }
      iris.tables.filterTable.call(this);
    },

    events: function(){
      var data = this.data,
          $table = data.$table;

      $table.on('click', 'tbody tr[data-route]', function(e){
        if (e.target.tagName !== 'A') {
          if ((e.ctrlKey || e.metaKey)) {
            window.open('/messages/' + $(this).attr('data-route'));
          } else {
            window.location = '/messages/' + $(this).attr('data-route');
          }
        }
      });
      data.$filterForm.on('submit', iris.tables.filterTable.bind(this));
    },
    getData: function(params){
      //merge params and fields
      params['fields'] = this.data.fields;
      params['limit'] = iris.data.tableEntryLimit;

      return $.ajax({
        url: this.data.url,
        data: params,
        traditional: true
      }).fail(function(){
        iris.createAlert('No messages found');
      });
    },
    initFilters: function(){
      for (var i = 0; i < window.appData.applications.length; i++) {
        this.data.$filterApp.append($(document.createElement('option')).attr({ value: window.appData.applications[i].name }).text(window.appData.applications[i].name));
      }
      for (i = 0; i < window.appData.priorities.length; i++) {
        this.data.$filterPriority.append($(document.createElement('option')).attr({ value: window.appData.priorities[i].name }).text(window.appData.priorities[i].name));
      }
      iris.typeahead.init('user');
      $('.datetimepicker').datetimepicker({
        showClose: true,
        keyBinds: {'delete': null}
      });
      // $('#filter-start').data('DateTimePicker').date(moment().subtract(1, 'hours'));
    }
  },
  message: {
    data: {
      url: '/v0/messages/',
      $page: $('.main'),
      incidentSource: $('#message-template').html()
    },
    init: function(){
      var location = window.location.pathname.split('/'),
          path = this.data.id = location[location.length - 1];
      this.getMessage(path);
    },
    getMessage: function(path){
      var self = this,
          template = this.data.template = Handlebars.compile(this.data.incidentSource),
          template_vars = {changes: []};
      $.getJSON(self.data.url + path).done(function(data) {
          if (data.generic_message_sent_status != null) {
              data.generic_message_sent_status = data.generic_message_sent_status ? 'sent' : 'failed to send';
          }
          $.extend(template_vars, data);
          $.getJSON(self.data.url + path + '/auditlog').done(function(data) {
            data.forEach(function(change) {
              var old_halves = change.old.split('|');
              if (old_halves.length == 2) {
                change.old = old_halves[1];
                change.old_role = old_halves[0];
              }
              change.change_type = change.change_type.split('-')[0];
            });
            template_vars.changes = data;
          }).always(function() {
            self.data.$page.html(template(template_vars));
            iris.changeTitle('Message #' + template_vars.id);
          });
      }).fail(function() {
          iris.createAlert('Message not found');
      });
    }
  },
    user: {
        data: {
            url: '/v0/users/',
            modesUrl: '/v0/modes',
            apiBase: '/v0/',
            postModesUrl: '/v0/users/modes/',
            reprioritizationUrl: '/v0/users/reprioritization/',
            settingsUrl: '/v0/users/settings/',
            overridesUrl: '/v0/users/overrides/',
            timezonesUrl: '/v0/timezones',
            user: window.appData.user,
            settings: null,
            reprioritizationSettings: [],
            supportedTimezones: [],
            supportedOverrideModes: [],
            $page: $('.main'),
            $priority: $('#priority-table'),
            $customOverrideTable: $('#custom-override-table'),
            $customOverrideModal: $('#custom-override-modal-content'),
            $batching: $('#batching-table'),
            $contact: $('.user-contact-module'),
            $saveBtn: $('#save-settings'),
            $saveModalBtn: $('#save-custom-override-modal'),
            $delOverrideBtn: $('#delete-override'),
            $reprioritizationToggleBtn: $('#reprioritization h4'),
            $reprioritizationAddBtn: $('#reprio-add-btn'),
            $reprioritizationTable: $('#reprioritization-table'),
            $addAppSelect: $('#add-application-select'),
            $addAppOverrideSelect: $('#add-application-override-select'),
            $addAppBtn: $('#add-application-button'),
            $addAppOverrideBtn: $('#add-application-override-button'),
            appsToDelete: {},
            priorityTemplate: $('#priority-template').html(),
            customOverrideTemplate: $('#custom-override-template').html(),
            createCustomOverrideModalTemplate: $('#custom-override-modal-template').html(),
            batchingTemplate: $('#batching-template').html(),
            subheaderTemplate: $('#user-contact-template').html(),
            reprioritizationTemplate: $('#reprioritization-table-template').html(),
            postModel: {},
            $timezoneSelect: $('#timezone-select'),
            $timezoneSave: $('#timezone-save'),
            $smsOverrideSelect: $('#sms-override-select'),
            $smsOverrideSave: $('#sms-override-save')
        },
        init: function(){
            iris.changeTitle('Settings');
            var self = this;
            this.supportedOverrideModes = window.appData.modes;
            // drop is ommitted add it for override options
            this.supportedOverrideModes.push('drop');

            this.getUserSettings().done(function(){
                self.getCustomOverrideSettings().done(function(){
                    self.createCustomOverrideTable();
                });
                self.createContactModule();
                self.createPriorityTable();
                self.populateSmsOverride();
                self.events();
            });
            this.getReprioritizationSettings().done(function(){
                self.populateReprioritization();
            });
            this.loadSupportedTimezones().done(function(){
                self.populateTimezone();
            });
        },
        events: function(){
            var self = this;
            this.data.$saveBtn.on('click', function(){
                self.saveSetting();
            });
            this.data.$saveModalBtn.on('click', function(){
                self.saveModal();
            });
            this.data.$delOverrideBtn.on('click', function() {
                self.deletePerCustomApp($(this).attr('data-app'));
            });
            this.data.$reprioritizationAddBtn.on('click', function(){
                $(this).prop('disabled', true);
                self.saveReprioritizationSettings();
            });
            this.data.$reprioritizationToggleBtn.on('click', function(){
                self.toggleReprioritization();
            });
            this.data.$addAppBtn.on('click', function(){
                self.addApplication();
            });
            this.data.$addAppOverrideBtn.on('click', function(){
                self.addApplicationOverride();
                self.data.$addAppOverrideBtn.prop('disabled', true);
            });
            this.data.$addAppSelect.change(function() {
                self.data.$addAppBtn.prop('disabled', $(this).val() == '');
            });
            this.data.$addAppOverrideSelect.change(function() {
                self.data.$addAppOverrideBtn.prop('disabled', $(this).val() == '');
            });
            this.data.$timezoneSelect.change(function() {
                self.data.$timezoneSave.prop('disabled', $(this).val() == '');
            });
            this.data.$timezoneSave.on('click', function(){
                self.saveTimezone();
            });
            this.data.$smsOverrideSelect.change(function() {
              self.data.$smsOverrideSave.prop('disabled', $(this).val() == '');
            });
            this.data.$smsOverrideSave.on('click', function(){
                self.saveSmsOverride();
                self.data.$smsOverrideSave.prop('disabled', true);
            });
            self.data.$saveBtn.prop('disabled', true);
            self.data.$addAppOverrideBtn.prop('disabled', true);
            self.data.$addAppBtn.prop('disabled', true);
        },
        getUserSettings: function() {
            var self = this;
            return $.getJSON(this.data.url + this.data.user).done(function(response) {
                self.data.settings = response;
                //add app data to settings.
                self.data.settings.priorities = window.appData.priorities;
                self.data.settings.modeSet = window.appData.modes;
                self.data.settings.applications = window.appData.applications;
            }).fail(function(response) {
                iris.createAlert('Error: Failed to load data -' + response.text);
            });
        },
        toggleReprioritization: function() {
            $('#reprioritization').toggleClass('active')
        },
        getReprioritizationSettings: function() {
            var self = this;
            return $.getJSON(this.data.reprioritizationUrl + this.data.user).done(function(response){
                self.data.reprioritizationSettings = response;
            }).fail(function(response){
                iris.createAlert('Error: Failed to load reprioritization data -' + response.text);
            });
        },
        getCustomOverrideSettings: function() {
            var self = this;
            return $.getJSON(this.data.url + this.data.user + '/categories').done(function(response){
                self.data.settings.categories = response;
                self.data.settings['customApp'] = new Set();
                self.data.settings.categories.forEach(function (item, index) {
                    self.data.settings.customApp.add(item['application']);
                });

            }).fail(function(response){
                iris.createAlert('Error: Failed to load notification category data -' + response.text);
            });
        },
        saveReprioritizationSettings: function() {
            var data = {},
                self = this;
            $('#reprioritization input, #reprioritization select').each(function() {
                data[$(this).data('type')] = $(this).val();
            });
            data['duration'] *= 60;
            $.ajax({
                url: this.data.reprioritizationUrl + this.data.user,
                data: JSON.stringify(data),
                method: 'POST',
                contentType: 'application/json'
            }).done(function(){
                iris.createAlert('Reprioritization added.', 'success');
                self.getReprioritizationSettings().done(function(){
                    self.populateReprioritization();
                });
            }).fail(function(response){
                iris.createAlert('Failed to add reprioritization: ' + response.responseJSON.description, 'danger');
            }).always(function(){
                self.data.$reprioritizationAddBtn.prop('disabled', false);
            });
        },
        deleteReprioritizationSetting: function(src_mode) {
            var self = this;
            $.ajax({
                url: this.data.reprioritizationUrl + this.data.user + '/' + src_mode,
                method: 'DELETE',
                contentType: 'application/json',
                data: '{}'
            }).done(function(){
                iris.createAlert('Reprioritization rule deleted.', 'success');
                self.getReprioritizationSettings().done(function(){
                    self.populateReprioritization();
                });
            }).fail(function(){
                iris.createAlert('Failed deleting', 'danger');
            });
        },
        populateReprioritization: function() {
            $('#reprioritization select').each(function(){
                var frag = '';
                window.appData.modes.forEach(function(mode) {
                    frag += ['<option>', mode, '</option>'].join('');
                });
                $(this).html(frag)
            });
            $('#reprio-dest-mode').val('sms');

            if (!this.data.reprioritizationSettings.length) {
                this.data.$reprioritizationTable.hide();
                return;
            }

            var existingReprioTemplate = Handlebars.compile(this.data.reprioritizationTemplate);
            this.data.$reprioritizationTable.html(existingReprioTemplate(this.data.reprioritizationSettings));
            this.data.$reprioritizationTable.show();

            var self = this;

            $('#reprioritization-table button').click(function(){
                self.deleteReprioritizationSetting($(this).data('src-mode'));
            });
        },
        createContactModule: function(){
            var template = Handlebars.compile(this.data.subheaderTemplate),
                settings = this.data.settings;
            this.data.$contact.html(template(settings));
        },
        createPriorityTable: function(){
            var template = Handlebars.compile(this.data.priorityTemplate),
                $priority = this.data.$priority,
                settings = this.data.settings,
                self = this;
            var global_default_values = {};
            var app_default_values = {};
            var app_supported_modes = {};
            settings.per_app_defaults = {};
            window.appData.priorities.forEach(function(priority) {
                global_default_values[priority.name] = priority.default_mode;
            });
            window.appData.applications.forEach(function(app) {
                app_default_values[app.name] = app.default_modes;
                app_supported_modes[app.name] = app.supported_modes;
            });
            settings.per_app_defaults_obj = {};
            for (var app in settings.per_app_modes) {
                settings.per_app_defaults[app] = {priorities: [], supported_modes: app_supported_modes[app]};     // Needed for handlebars
                settings.per_app_defaults_obj[app] = {}; // Needed for JS elsewhere
                window.appData.priorities.forEach(function(p) {
                    var priority = p.name;
                    var default_mode = app_default_values[app][priority] ? app_default_values[app][priority] : (
                        global_default_values[priority] ? global_default_values[priority] : ''
                    );
                    settings.per_app_defaults[app].priorities.push({
                        priority_name: priority,
                        default_mode: default_mode
                    });
                    settings.per_app_defaults_obj[app][priority] = default_mode;
                });
            }
            this.data.$priority.empty();
            this.data.$priority.append(template(settings));
            //load saved user settings to ui, and make changing any of them enable the save button
            $priority.find('select').each(function(){
                var priority = $(this).data('type'),
                    app = $(this).data('app'),
                    setting;
                if (app) {
                    setting = settings.per_app_modes[app][priority] ? settings.per_app_modes[app][priority] : 'default';
                } else {
                    setting = settings.modes[priority] ? settings.modes[priority] : 'default';
                }
                $(this).val(setting);
                // On dropdown change state, modify our settings dictionaries so the next table redraw shows
                // the changed settings
                $(this).change(function() {
                    self.data.$saveBtn.prop('disabled', false);
                    var val = $(this).val();
                    if (app) {
                        settings.per_app_modes[app][priority] = val;
                    }
                    else {
                        // Our per-app dropdowns do not have default, so don't bother
                        if (val == 'default') {
                            delete settings.modes[priority];
                        } else {
                            settings.modes[priority] = val;
                        }
                    }
                });
            });
            $priority.find('button.delete-app-button').each(function() {
                $(this).click(function() {
                    self.deletePerApp($(this));
                });
            });
            this.redrawApplicationDropdown();
        },
        createCustomOverrideTable: function(){
            var template = Handlebars.compile(this.data.customOverrideTemplate),
                settings = this.data.settings,
                self = this;
            this.data.$customOverrideTable.empty();
            this.data.$customOverrideTable.append(template(settings));
            this.data.$customOverrideTable.find('button.delete-custom-app-button').each(function() {
                $(this).click(function() {
                    var appToDelete = $(this).data('app');
                    $('#app-overrides-to-delete').text(appToDelete);
                    $('#delete-override').attr('data-app', appToDelete);
                    $('#confirm-delete-override').modal('show');
                });
            });

            this.data.$customOverrideTable.find('button.edit-custom-app-button').each(function() {
                $(this).click(function() {
                    self.editPerCustomApp($(this));
                });
            });

            this.redrawApplicationOverrideDropdown();
        },
        createCustomOverrideModal: function(app){

            var template = Handlebars.compile(this.data.createCustomOverrideModalTemplate),
                self = this,
                settings = this.data.settings,
                customOverrideModal = this.data.$customOverrideModal;

            // call out to the back end to get all categories for this app
            var appOverrideCategories = [];
            $.ajax({
                type: "GET",
                url: '/v0/categories/' + app
            }).done(function (resp) {
                  appOverrideCategories = resp;
                  appOverrideCategories.forEach(function (appSetting, i) {
                    settings.categories.forEach(function (userSetting) {
                      if(appSetting['application'] === userSetting['application'] && appSetting['name'] === userSetting['category']){
                        //apply user overrides
                        appOverrideCategories[i]['mode'] = userSetting['mode'];
                      }
                    });
                  });
                  settings['modalAppName'] = app;
                  settings['appCategoryData'] = appOverrideCategories;
                  settings['supported_modes'] = self.supportedOverrideModes;
                  customOverrideModal.empty();
                  customOverrideModal.append(template(settings));
                  $('#custom-override-modal').modal('show');
            }).fail(function(){
                iris.createAlert('Failed to fetch category data for this app', 'danger');
            });

        },
        createBatchingTable: function(){
            var template = Handlebars.compile(this.data.batchingTemplate),
                settings = this.data.settings;
            this.data.$batching.append(template(settings));
        },
        deletePerApp: function(elem) {
            var self = this,
                app = elem.data('app');
            self.data.$saveBtn.prop('disabled', false);
            delete self.data.settings.per_app_modes[app];
            self.data.appsToDelete[app] = true;
            self.createPriorityTable();
        },
        deletePerCustomApp: function(app) {
            var self = this;

            if(self.data.settings.customApp.has(app)){
                // delete user overrides for application
                $.ajax({
                    url: self.data.url + self.data.user + '/categories/' + app,
                    method: 'DELETE',
                    contentType: 'text'
                }).done(function(){
                    // delete user mode overrides locally
                    self.data.settings.categories = self.data.settings.categories.filter(function( obj ) {
                        return obj.application !== app;
                    });
                    self.data.settings.customApp.delete(app);
                    iris.createAlert('Deleted application succesfully', 'success');
                    self.createCustomOverrideTable();
                }).fail(function(){
                    iris.createAlert('Failed to delete application', 'danger');
                });
            }
        },
        editPerCustomApp: function(elem) {
            var app = elem.data('app');
            this.createCustomOverrideModal(app);
        },
        saveSetting: function(){
            var globalOptions = this.data.postModel,
                self = this;
            self.data.$saveBtn.prop('disabled', true);
            //get form data
            $('#priority-table select.global-priority').each(function(){
                var $this = $(this);
                globalOptions[$this.attr('data-type')] = $this.val();
            });

            globalOptions.per_app_modes = {};

            $('#priority-table tr.app-row').each(function() {
                var app = $(this).data('app'),
                    all_default = true;

                globalOptions.per_app_modes[app] = {};

                $(this).find('select.app-priority').each(function() {
                    var $this = $(this),
                        val = $this.val();
                    globalOptions.per_app_modes[app][$this.attr('data-type')] = val;
                    if (val != 'default') {
                        all_default = false;
                    }
                });

                // If the user chooses 'default' for all values, set each one to the default value for that app or column to avoid the row
                // disappearing on reload (as all 'default' deletes the custom setting)
                if (all_default) {
                    for (var key in globalOptions.per_app_modes[app]) {
                        globalOptions.per_app_modes[app][key] = self.data.settings.per_app_defaults_obj[app][key];
                    }
                }
            });

            for (var app in self.data.appsToDelete) {
                globalOptions.per_app_modes[app] = {};
                self.data.settings.priorities.forEach(function(p) {
                    globalOptions.per_app_modes[app][p.name] = 'default';
                });
            }

            self.data.appsToDelete = {};

            $.ajax({
                url: this.data.postModesUrl + this.data.user,
                data: JSON.stringify(globalOptions),
                method: 'POST',
                contentType: 'application/json'
            }).done(function(){
                iris.createAlert('Settings saved.', 'success');
            }).fail(function(){
                iris.createAlert('Failed to save settings', 'danger');
            });
        },
        saveModal: function(){
            var modalOptions = {},
                self = this,
                settings = this.data.settings,
                app = $('#custom-override-modal-table').data('app');

            $('select.custom-modal-priority').each(function() {
                var $this = $(this),
                    val = $this.val();
                modalOptions[$this.data('category')] = val;
            });

            $.ajax({
                url: this.data.url + this.data.user + '/categories/' + app,
                data: JSON.stringify(modalOptions),
                method: 'POST',
                contentType: 'text'
            }).done(function(){
                iris.createAlert('Modal settings saved succesfully', 'success');
                self.data.settings.customApp.add(app);

                // update user overrides
                settings.categories.forEach(function(cat, i){
                    if(cat['application'] == app){
                        self.data.settings.categories.splice(i,1);
                    }
                });
                Object.keys(modalOptions).forEach(function(key) {
                    self.data.settings.categories.push({ 'application': app, 'category': key, 'mode': modalOptions[key]});
                });

                self.createCustomOverrideTable();

            }).fail(function(){
                iris.createAlert('Failed to save modal settings', 'danger');
            });
        },
        redrawApplicationDropdown: function() {
            var self = this;
            self.data.$addAppSelect.empty();
            self.data.$addAppSelect.append($('<option value="">').text('Add Application'));
            var myApps = Object.keys(self.data.settings.per_app_modes);
            this.data.settings.applications.sort(function(app1, app2) {
                var app1_name = app1.name.toLowerCase(),
                    app2_name = app2.name.toLowerCase();
                if (app1_name > app2_name) {
                    return 1;
                } else if (app2_name > app1_name) {
                    return -1;
                } else {
                    return 0;
                }
            }).forEach(function(app) {
                if (myApps.indexOf(app.name) == -1) {
                    self.data.$addAppSelect.append($('<option>').text(app.name));
                }
            });
        },
        addApplication: function() {
            var app = this.data.$addAppSelect.val();
            this.data.$addAppSelect.val('');
            this.data.$addAppBtn.prop('disabled', true);
            if (app == '') {
                return;
            }
            this.data.$saveBtn.prop('disabled', false);
            this.data.settings.per_app_modes[app] = {};
            if (app in this.data.appsToDelete) {
                delete this.data.appsToDelete[app];
            }
            this.createPriorityTable();
        },
        addApplicationOverride: function() {
            var app = this.data.$addAppOverrideSelect.val();
            this.data.$addAppOverrideSelect.val('');
            this.createCustomOverrideModal(app);

        },
        redrawApplicationOverrideDropdown: function() {
            var self = this,
                customOverrideApps = new Set;

            //fetch apps that have custom categories defined
            $.ajax({
                type: "GET",
                url: '/v0/categories/'
            }).done(function (resp) {
                  self.data.$addAppOverrideSelect.empty();
                  self.data.$addAppOverrideSelect.append($('<option value="">').text('Add Application'));
                  var appOverrideCategories = resp;
                  appOverrideCategories.forEach(function (appSetting, i) {
                    customOverrideApps.add(appSetting['application']);
                  });
                  Array.from(customOverrideApps).sort().forEach(function (app) {
                    self.data.$addAppOverrideSelect.append($('<option>').text(app));
                  });

              }).fail(function () {
                iris.createAlert('Failed to fetch applications for dropdown', 'danger');
              });

        },
        loadSupportedTimezones: function() {
            var self = this;
            return $.getJSON(this.data.timezonesUrl).done(function(response){
                self.data.supportedTimezones = response;
            }).fail(function(response){
                iris.createAlert('Error: Failed to load supported timezones -' + response.text);
            });
        },
        saveTimezone: function() {
            $.ajax({
                url: this.data.settingsUrl + this.data.user,
                data: JSON.stringify({'timezone': this.data.$timezoneSelect.val()}),
                method: 'PUT',
                contentType: 'application/json'
            }).done(function(){
                iris.createAlert('Settings saved.', 'success');
            }).fail(function(){
                iris.createAlert('Failed to save settings', 'danger');
            });
        },
        populateTimezone: function() {
            var self = this,
                configured_timezone = window.appData.user_settings.timezone;
            self.data.$timezoneSelect.empty();
            if (!configured_timezone) {
                self.data.$timezoneSelect.append($('<option value="">').text('Browser Default'));
                self.data.$timezoneSave.prop('disabled', true);
            }
            self.data.supportedTimezones.forEach(function(name) {
                self.data.$timezoneSelect.append($('<option>').text(name));
            });
            if (configured_timezone) {
                self.data.$timezoneSelect.val(configured_timezone);
            }
        },
        saveSmsOverride: function() {
            $.ajax({
                url: this.data.overridesUrl + this.data.user,
                data: JSON.stringify({'template_overrides': {'sms':this.data.$smsOverrideSelect.val()}}),
                method: 'POST',
                contentType: 'application/json'
            }).done(function(){
                iris.createAlert('Settings saved.', 'success');
            }).fail(function(){
                iris.createAlert('Failed to save settings', 'danger');
            });
        },
        populateSmsOverride: function() {
            var self = this;
            var overrideBool = false;

            if ('template_overrides' in self.data.settings){
              overrideBool =  self.data.settings.template_overrides.includes('sms');
            }
            self.data.$smsOverrideSelect.empty();
            if (!overrideBool) {
              self.data.$smsOverrideSelect.append($('<option value="disabled">').text('Disabled (Default)'));
              self.data.$smsOverrideSelect.append($('<option value="enabled">').text('Enabled'));
              self.data.$smsOverrideSave.prop('disabled', true);
            }
            else {
              self.data.$smsOverrideSelect.append($('<option value="enabled">').text('Enabled'));
              self.data.$smsOverrideSelect.append($('<option value="disabled">').text('Disabled (Default)'));
              self.data.$smsOverrideSave.prop('disabled', true);
            }
        }
    }, //end iris.user
    applications: {
        data: {
            $page: $('.main'),
            $table: $('#applications-table'),
            $pageHeader: $('.main h3'),
            $createAppModal: $('#create-app-modal'),
            showAppModalButton: '#show-app-modal-button',
            applicationSubmitButton: '#create-app-submit',
            tableRows: 'tbody tr',
            tableTemplate: $('#applications-table-template').html(),
            headerTemplate: $('#applications-header-template').html(),
            DataTable: null,
            dataTableOpts: {
                orderClasses: false,
                order: [[0, 'asc']]
            }
        },
        init: function() {
            iris.changeTitle('Applications');

            this.data.$pageHeader.html(Handlebars.compile(this.data.headerTemplate)({
                showCreateButton: window.appData.user_admin
            }));

            iris.tables.createTable.call(this, window.appData.applications);
            this.events();
        },
        events: function() {
            this.data.$page.on('click', this.data.tableRows, function() {
                window.location = '/applications/' + $(this).data('application');
            });
            this.data.$page.on('click', this.data.showAppModalButton, this.showCreateAppModal.bind(this));
            this.data.$page.on('click', this.data.applicationSubmitButton, this.createApplication.bind(this));
        },
        showCreateAppModal: function() {
            this.data.$createAppModal.modal();
        },
        createApplication: function() {
            var self = this,
                $appNameBox = $('#create-app-name'),
                appName = $.trim($appNameBox.val()),
                appNameLower = appName.toLowerCase();

            if (appName == '') {
                $appNameBox.val('');
                $appNameBox.focus();
                return;
            }

            // If this application already exists, just go to its page
            for (var i = 0; i < window.appData.applications.length; i++) {
                if (window.appData.applications[i].name.toLowerCase() == appNameLower) {
                    window.location = '/applications/' + window.appData.applications[i].name;
                    return;
                }
            }

            $.ajax({
                url: '/v0/applications/',
                data: JSON.stringify({
                    name: appName
                }),
                method: 'POST',
                contentType: 'application/json'
            }).done(function() {
                window.location = '/applications/' + appName
            }).fail(function(r) {
                iris.createAlert('Failed creating application: ' + r.responseJSON['title'])
            }).always(function() {
                self.data.$createAppModal.modal('hide');
            });
        }
    }, // End iris.applications
    application: {
        data: {
            url: '/v0/applications/',
            apiBase: '/v0/',
            $page: $('.main'),
            $editButton: $('#application-edit-button'),
            applicationTemplate: $('#application-template').html(),
            loaderTemplate: $('#loader-template').html(),
            applicationEditbutton: '#application-edit-button',
            applicationSavebutton: '#application-save-button',
            applicationRenameButton: '#application-rename-button',
            applicationDeleteButton: '#application-delete-button',
            applicationRekeyButton: '#application-rekey-button',
            applicationSecondaryKeyButton: '#application-secondary-key-button',
            showRenameModalButton: '#show-rename-modal-button',
            showDeleteModalButton: '#show-delete-modal-button',
            showRekeyModalButton: '#show-rekey-modal-button',
            showSecondaryKeyModalButton: '#show-secondary-key-modal-button',
            removeVariableButton: '.remove-variable',
            removeOwnerButton: '.remove-owner',
            removeAddressButton: '.remove-address',
            showApiKeyButton: '#show-api-key-button',
            showSecondaryKeyButton: '#show-secondary-key-button',
            addVariableForm: '#add-variable-form',
            addOwnerForm: '#add-owner-form',
            addAddressForm: '#add-address-form',
            addEmailIncidentForm: '#add-email-incident-form',
            addCustomCategoryForm: '#add-custom-category-form',
            addDefaultModeForm: '#add-default-mode-form',
            removeEmailIncidentButton: '.delete-email-incident-button',
            removeCustomCategoryButton: '.delete-custom-category-button',
            removeDefaultModeButton: '.delete-default-mode-button',
            dangerousActionsToggle: '.application-dangerous-actions h4',
            application: null,
            model: {}
        },
        init: function() {
            var location = window.location.pathname.split('/'),
                application = decodeURIComponent(location[location.length - 1]);

            // Register this only for this page because it isn't used anywhere else. Only admins and users
            // can delete owners, but users who are not admins cannot delete themselves.
            Handlebars.registerHelper('ifCanShowDeleteUserButton', function(username, opts) {
                return window.appData.user_admin || username != window.appData.user ? opts.fn(this) : opts.inverse(this);
            });

            this.data.application = application;
            this.getApplication(application);
        },
        events: function() {
            var self = this,
                data = this.data;
            data.$page.on('click', data.applicationEditbutton, this.editApplication.bind(this));
            data.$page.on('click', data.applicationSavebutton, this.saveApplication.bind(this));
            data.$page.on('click', data.showRenameModalButton, this.showRenameModal.bind(this));
            data.$page.on('click', data.showDeleteModalButton, this.showDeleteModal.bind(this));
            data.$page.on('click', data.showRekeyModalButton, this.showRekeyModal.bind(this));
            data.$page.on('click', data.showSecondaryKeyModalButton, this.showSecondaryKeyModal.bind(this));
            data.$page.on('click', data.applicationRenameButton, this.renameApplication.bind(this));
            data.$page.on('click', data.applicationDeleteButton, this.deleteApplication.bind(this));
            data.$page.on('click', data.applicationRekeyButton, this.rekeyApplication.bind(this));
            data.$page.on('click', data.applicationSecondaryKeyButton, this.genSecondaryKey.bind(this));
            data.$page.on('click', data.showApiKeyButton, this.showApiKey.bind(this));
            data.$page.on('click', data.showSecondaryKeyButton, this.showSecondaryKey.bind(this));
            data.$page.on('click', data.dangerousActionsToggle, this.toggleDangerousActions.bind(this));
            data.$page.on('click', data.removeVariableButton, function() {
                var variable = $(this).data('variable');
                var pos = self.data.model.variables.indexOf(variable);
                if (pos !== -1) {
                    self.data.model.variables.splice(pos, 1)
                }
                $(this).parent().remove();
            });
            data.$page.on('click', data.removeOwnerButton, function() {
                var owner = $(this).data('owner');
                var pos = self.data.model.owners.indexOf(owner);
                if (pos !== -1) {
                    self.data.model.owners.splice(pos, 1)
                }
                $(this).parent().remove();
            });
            data.$page.on('click', data.removeAddressButton, function(e) {
                e.preventDefault();
                self.data.model.custom_sender_addresses.email = null;
                $("#custom-sender-email-value").text('None (using default sender address)');
            });
            data.$page.on('submit', data.addVariableForm, function(e) {
                e.preventDefault();
                var variable = $('#add-variable-box').val();
                if (variable == '') {
                    iris.createAlert('Cannot add empty variable');
                    return;
                }
                if (self.data.model.variables.indexOf(variable) !== -1) {
                    iris.createAlert('That variable "' + variable + '" already exists');
                    return;
                }
                $('#add-variable-box').val('');
                self.data.model.variables.push(variable);
                self.modelPersist();
                self.render();
            });
            data.$page.on('submit', data.addOwnerForm, function(e) {
                e.preventDefault();
                var owner = $('#add-owner-box').val();
                if (owner == '') {
                    iris.createAlert('Cannot add empty owner');
                    return;
                }
                if (self.data.model.owners.indexOf(owner) !== -1) {
                    iris.createAlert('That owner "' + owner + '" already exists');
                    return;
                }
                $('#add-owner-box').val('');
                self.data.model.owners.push(owner);
                self.modelPersist();
                self.render();
            });
            data.$page.on('submit', data.addAddressForm, function(e) {
                e.preventDefault();
                var address = $('#add-address-box').val();
                if (address === '') {
                    iris.createAlert('Cannot add empty custom address');
                    return;
                }
                if(self.validateEmail(address) === false){
                    iris.createAlert('Email address is invalid. Please make sure it is formatted correctly.');
                    return;
                }

                $('#add-address-box').val('');
                self.data.model.custom_sender_addresses.email = address;
                self.modelPersist();
                self.render();
            });
            data.$page.on('submit', data.addEmailIncidentForm, function(e) {
                e.preventDefault();
                var $email = $('#add-email-incident-email');
                var $plan = $('#add-email-incident-plan');
                self.data.model.emailIncidents[$email.val()] = $plan.val();
                $email.val('');
                $plan.val('');
                self.modelPersist();
                self.render();
            });
            data.$page.on('click', data.removeEmailIncidentButton, function() {
                delete self.data.model.emailIncidents[$(this).data('email')];
                self.modelPersist();
                self.render();
            });
            data.$page.on('submit', data.addCustomCategoryForm, function(e) {
                e.preventDefault();
                var $category = $('#add-custom-category');
                var $description = $('#add-custom-category-description');
                var $mode = $('#category-default-mode');
                self.data.model.customCategories.forEach(function(element, i){
                    // if it already exists, replace with new values
                    if (element["name"] == $category.val()){
                        self.data.model.customCategories.splice(i, 1);
                    }
                });
                self.data.model.customCategories.push({"name":$category.val(), "description": $description.val(), "mode": $mode.val()});
                $category.val('');
                $description.val('');
                self.modelPersist();
                self.render();
            });
            data.$page.on('click', data.removeCustomCategoryButton, function() {
                var nameToDelete = $(this).data('category');
                self.data.model.customCategories.forEach(function(element, i){
                    if(element["name"] == nameToDelete){
                        self.data.model.customCategories.splice(i, 1);
                    }
                });
                self.modelPersist();
                self.render();
            });
            data.$page.on('submit', data.addDefaultModeForm, function(e) {
                e.preventDefault();
                var $priority = $('#default-mode-form-priority'),
                    priority_val = $priority.val();
                var $mode = $('#default-mode-form-mode'),
                    mode_val = $mode.val();
                if (priority_val == '') {
                    $priority.addClass('invalid-input');
                    return;
                } else {
                    $priority.removeClass('invalid-input');
                }
                if (mode_val == '') {
                    $mode.addClass('invalid-input');
                    return;
                } else {
                    $mode.removeClass('invalid-input');
                }
                self.data.model.default_modes[priority_val] = mode_val;
                $priority.val('');
                $mode.val('');
                self.modelPersist();
                self.render();
            });
            data.$page.on('click', data.removeDefaultModeButton, function() {
                delete self.data.model.default_modes[$(this).data('priority')];
                self.modelPersist();
                self.render();
            });
            window.onbeforeunload = iris.unloadDialog.bind(this);
        },
        validateEmail: function(email) {
            var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
            return re.test(String(email).toLowerCase());
        },
        modelPersist: function() {
            var self = this;
            self.data.$page.find('textarea').each(function() {
                var key = $(this).data('field');
                if (key && key in self.data.model) {
                    self.data.model[key] = $(this).val();
                }
            });
        },
        getApplication: function(application) {
            var app = null,
                self = this,
                applicationLower = application.toLowerCase();
            for (var i = 0, item; i < window.appData.applications.length; i++) {
                item = window.appData.applications[i];
                if (item.name.toLowerCase() == applicationLower) {
                    app = item;
                    break;
                }
            }
            if (!app) {
                iris.createAlert('Application not found');
                return;
            }
            iris.changeTitle('Application ' + app.name);

            self.showLoader();

            $.when($.get(self.data.url + application + '/quota'),
                $.get(self.data.url + application + '/incident_emails'),
                $.get(self.data.apiBase + 'categories/' + self.data.application)
            ).always(function(quota, incident_emails, customCategories) {
                app.quota = Object.keys(quota[0]).length ? quota[0] : null;
                app.emailIncidents = incident_emails[0];

                app.customCategories = [];
                customCategories[0].forEach(function(element){
                    app.customCategories.push({'name':element['name'], 'description':element['description'], 'mode':element['mode']})
                });

                // For convenience in setting the below boolean flags, localize
                // whether the user is an owner of this app or is an admin here.
                var isOwner = app.owners.indexOf(window.appData.user) !== -1;
                var isAdmin = window.appData.user_admin;

                // Bunch of boolean flags passed to the template which control what is
                // seen and how the UI behaves. The entire template is scattered with if
                // blocks based on these variables.
                app.isInViewMode = true;
                app.isEditable = isAdmin || isOwner;
                app.allowViewingKey = isAdmin || isOwner;
                app.allowEditingEmailIncidents = isAdmin || isOwner;
                app.allowEditingCustomCategories = isAdmin || isOwner;
                app.showEditOwners = isAdmin || isOwner;
                app.allowDangerousActions = isAdmin || isOwner;
                app.allowEditingSupportedModes = isAdmin;
                app.allowEditingTitle = isAdmin || isOwner;

                // This gets turned to true when the edit button is clicked if the user
                // is an admin
                app.showEditQuotas = false;

                app.apiKey = false;
                app.priorities = window.appData.priorities.map(function(priority) {
                    return priority.name;
                });
                app.modes = window.appData.modes;
                self.data.model = app;
                self.render();
                self.events();
            }).fail(function() {
                iris.createAlert('Failed loading app settings');
            });
        },
        editApplication: function() {
            this.data.model.isInViewMode = false;
            this.data.model.showEditQuotas = window.appData.user_admin;
            this.render();
        },
        showApiKey: function() {
            var self = this;
            $(self.data.showApiKeyButton).prop('disabled', true);
            $.get('/v0/applications/' + self.data.application + '/key').done(function(result) {
                self.data.model.apiKey = result.key;
                self.modelPersist();
                self.render();
            }).fail(function(result) {
                iris.createAlert('Unable to get key: ' + result.responseJSON.title);
            });
        },
        showSecondaryKey: function() {
            var self = this;
            $(self.data.showSecondaryKeyButton).prop('disabled', true);
            $.get('/v0/applications/' + self.data.application + '/secondary').done(function(result) {
                self.data.model.secondaryKey = result.key;
                if (result.key === null) {
                    self.data.model.secondaryKey = 'No secondary key exists'
                }
                self.modelPersist();
                self.render();
            }).fail(function(result) {
                iris.createAlert('Unable to get key: ' + result.responseJSON.title);
            });
        },
        saveApplication: function() {
            var self = this,
                failedCheck = false;
            $('.application-settings').find('textarea').each(function(k, elem) {
                var $elem = $(elem),
                    field = $elem.data('field'),
                    val = $elem.val();
                self.data.model[field] = val;
                $elem.removeClass('invalid-input');
                if (field == 'context_template' || field == 'summary_template' || field == 'mobile_template') {
                    try {
                        Handlebars.compile(val)({})
                    } catch (e) {
                        iris.createAlert('Invalid HandleBars syntax for ' + field + '.\n' + e.message);
                        $elem.addClass('invalid-input');
                        failedCheck = true;
                    }
                } else if (field == 'sample_context' && val != '') {
                    try {
                        JSON.parse(val);
                    } catch (e) {
                        iris.createAlert('Invalid JSON syntax for sample context.\n' + e.message);
                        $elem.addClass('invalid-input');
                        failedCheck = true;
                    }
                }
            });
            if (failedCheck) {
                return;
            }
            if (self.data.model.sample_context == '') {
                self.data.model.sample_context = '{}';
            }
            var ajaxCalls = [];
            if (self.data.model.showEditQuotas) {
                var quotaSettings = {},
                    deleteQuota = true;
                $('.application-quota').find('input').each(function(k, elem) {
                    var $elem = $(elem),
                        field = $elem.attr('name'),
                        val = $elem.val();
                    if (field && val != '' && val != '0') {
                        if (field != 'target_name' && field != 'plan_name') {
                            val = parseInt(val);
                        }
                        quotaSettings[field] = val;
                        deleteQuota = false;
                    }
                });
                if (deleteQuota) {
                    self.data.model.quota = null;
                    ajaxCalls.push($.ajax({
                        url: self.data.url + self.data.application + '/quota',
                        method: 'DELETE',
                        data: '{}',
                        contentType: 'application/json'
                    }));
                } else {
                    self.data.model.quota = quotaSettings;
                    quotaSettings.wait_time = 3600;
                    // Abstract away the fact that quota durations are really seconds underneath
                    quotaSettings.hard_quota_duration *= 60;
                    quotaSettings.soft_quota_duration *= 60;
                    ajaxCalls.push($.ajax({
                        url: self.data.url + self.data.application + '/quota',
                        data: JSON.stringify(quotaSettings),
                        method: 'POST',
                        contentType: 'application/json'
                    }));
                }
            }
            if (self.data.model.allowEditingEmailIncidents) {
                ajaxCalls.push($.ajax({
                    url: self.data.url + self.data.application + '/incident_emails',
                    data: JSON.stringify(self.data.model.emailIncidents),
                    method: 'PUT',
                    contentType: 'application/json'
                }));
            }
            if (self.data.model.allowEditingCustomCategories) {
                ajaxCalls.push($.ajax({
                    url: self.data.apiBase + 'categories/' + self.data.application,
                    data: JSON.stringify(self.data.model.customCategories),
                    method: 'POST',
                    contentType: 'application/json'
                }));
            }
            if (self.data.model.allowEditingSupportedModes) {
                self.data.model.supported_modes = [];
                $('input[name=supported_modes]').each(function(k, elem) {
                    var $elem = $(elem);
                    if ($elem.prop('checked')) {
                        self.data.model.supported_modes.push($elem.val());
                    }
                });
                // Remove any default modes using modes we no longer support
                for (var priority in self.data.model.default_modes) {
                    if (self.data.model.supported_modes.indexOf(self.data.model.default_modes[priority]) == -1) {
                        delete self.data.model.default_modes[priority];
                    }
                }
            }

            if (self.data.model.allowEditingTitle){
                self.data.model.title_variable = $('#title-variable-select').val();
                if(self.data.model.title_variable == 'null'){
                    self.data.model.title_variable = null;
                }
            }

            ajaxCalls.push($.ajax({
                url: self.data.url + self.data.application,
                data: JSON.stringify(self.data.model),
                method: 'PUT',
                contentType: 'application/json'
            }));
            $.when.apply(undefined, ajaxCalls).done(function(){
                self.data.model.isInViewMode = true;
                self.data.model.showEditQuotas = false;
                self.data.model.apiKey = false;
                self.render();
                iris.createAlert('Settings saved', 'success');
            }).fail(function(data) {
                iris.createAlert('Settings failed to save: ' + data.responseJSON.title);
            });
        },
        toggleDangerousActions: function() {
            $('.application-dangerous-actions').toggleClass('active')
        },
        showRenameModal: function() {
            $('#app-new-name-box').val(this.data.application);
            $('#rename-app-modal').modal();
        },
        showDeleteModal: function() {
            $('#delete-app-modal').modal();
        },
        showRekeyModal: function() {
            $('#rekey-app-modal').modal();
        },
        showSecondaryKeyModal: function() {
            $('#secondary-key-app-modal').modal();
        },
        renameApplication: function() {
            var $nameBox = $('#app-new-name-box'),
                newName = $.trim($nameBox.val());
            if (newName == '' || newName == this.data.application) {
                $nameBox.focus();
                return;
            }
            var $renameBtn = $(this.data.applicationRenameButton);
            $renameBtn.prop('disabled', true);
            $.ajax({
                url: '/v0/applications/' + this.data.application + '/rename',
                data: JSON.stringify({
                    new_name: newName
                }),
                method: 'PUT',
                contentType: 'application/json'
            }).done(function() {
                window.onbeforeunload = null;
                window.location = '/applications/' + newName;
            }).fail(function(r) {
                iris.createAlert('Failed renaming application: ' + r.responseJSON['title']);
                $('body').scrollTop(0);
                $renameBtn.prop('disabled', false);
            }).always(function() {
                $('#rename-app-modal').modal('hide');
            });
        },
        deleteApplication: function() {
            var $deleteBtn = $(this.data.applicationDeleteButton);
            $deleteBtn.prop('disabled', true);
            $.ajax({
                url: '/v0/applications/' + this.data.application,
                method: 'DELETE',
                contentType: 'application/json'
            }).done(function() {
                window.onbeforeunload = null;
                window.location = '/applications/';
            }).fail(function(r) {
                iris.createAlert('Failed deleting application: ' + r.responseJSON['title']);
                $('body').scrollTop(0);
                $deleteBtn.prop('disabled', false);
            }).always(function() {
                $('#delete-app-modal').modal('hide');
            });
        },
        rekeyApplication: function() {
            var $rekeyBtn = $(this.data.applicationRekeyButton);
            $rekeyBtn.prop('disabled', true);
            $.ajax({
                url: '/v0/applications/' + this.data.application + '/rekey',
                method: 'POST',
                contentType: 'application/json'
            }).done(function() {
                iris.createAlert('Successfully rekey\'d application', 'success')
            }).fail(function(r) {
                iris.createAlert('Failed re-keying application: ' + r.responseJSON['title'])
            }).always(function() {
                $('#rekey-app-modal').modal('hide');
                $('body').scrollTop(0);
                $rekeyBtn.prop('disabled', false);
            });
        },
        genSecondaryKey: function() {
            var $keyBtn = $(this.data.applicationRekeyButton);
            $keyBtn.prop('disabled', true);
            $.ajax({
                url: '/v0/applications/' + this.data.application + '/secondary',
                method: 'POST',
                contentType: 'application/json'
            }).done(function() {
                iris.createAlert('Successfully generated secondary key', 'success')
            }).fail(function(r) {
                iris.createAlert('Failed to generate secondary key: ' + r.responseJSON['title'])
            }).always(function() {
                $('#secondary-key-app-modal').modal('hide');
                $('body').scrollTop(0);
                $keyBtn.prop('disabled', false);
            });
        },
        showLoader: function() {
            var template = Handlebars.compile(this.data.loaderTemplate);
            this.data.$page.html(template(this.data.model));
        },
        render: function() {
            var template = Handlebars.compile(this.data.applicationTemplate);
            this.data.$page.html(template(this.data.model));
            if (this.data.model.showEditQuotas || this.data.model.showEditOwners) {
                iris.typeahead.init('');
            } else {
                iris.typeahead.destroy();
            }
        }
    }, // End iris.application
    stats: {
        data: {
            url: '/v0/stats',
            $page: $('.stats'),
            $table: $('#stats-table'),
            tableTemplate: $('#stats-table-template').html(),
            DataTable: null,
            dataTableOpts: {
                orderClasses: false,
                order: [[0, 'asc']],
                columns: [
                    null,
                    null
                ]
            }
        },
        init: function() {
            iris.changeTitle('Stats');
            iris.tables.filterTable.call(this);
        },
        events: function() {},
        getData: function(params) {
            return $.getJSON(this.data.url, params).fail(function(){
                iris.createAlert('No stats found');
            });
        }
    }, // End iris.stats
    stat: {
        data: {
            url: '/v0/applications/',
            $page: $('.stats'),
            $table: $('#stats-table'),
            application: null,
            tableTemplate: $('#stats-table-template').html(),
            DataTable: null,
            dataTableOpts: {
                orderClasses: false,
                order: [[0, 'asc']],
                columns: [
                    null,
                    null
                ]
            }
        },
        init: function() {
            var location = window.location.pathname.split('/'),
                application = decodeURIComponent(location[location.length - 1]);

            iris.changeTitle('App Stats');
            $('#stats-header').text("App Stats: " + application);
            this.data.application = application;
            iris.tables.filterTable.call(this);
        },
        events: function() {},
        getData: function(params) {
            apiUrl = this.data.url + this.data.application + "/stats";
            return $.getJSON(apiUrl).fail(function(){
                iris.createAlert('No stats found');
            });
        }
    }, // End iris.appStats
    unsubscribe: {
        data: {
          url: '/v0/applications/',
          $page: $('.unsub'),
          application: null,
          user: null,
          unsubscribeButton: $('#unsub-button'),
          unsubTemplate: $('#unsub-template').html(),
        },
        init: function() {
          var location = window.location.pathname.split('/'),
              application = decodeURIComponent(location[location.length - 1])
              self = this;

          iris.changeTitle('Unsubscribe');
          this.events()
          var template = Handlebars.compile(this.data.unsubTemplate);
          $.when($.get(self.data.url + application), $.get('/v0/users/' + window.appData.user)).then(function(app, user){
            app = app[0];
            self.data.application = app;
            self.data.user = user[0];
            self.data.$page.html(template({'name': app['name'], 'owners': app['owners'], 'eligible': app.supported_modes.includes('drop')}));
          }).fail(function(){
            iris.createAlert('Failed to fetch application data');
          })
        },
        events: function() {
          this.data.$page.on('click', this.data.unsubscribeButton, this.unsubscribe.bind(this));
        },
        unsubscribe: function() {
          var self = this,
              modes = self.data.user['modes']
          // Construct new user modes
          modes['per_app_modes'] = self.data.user['per_app_modes']
          modes['per_app_modes'][self.data.application['name']] = {};
          window.appData.priorities.forEach(function(priority){
            modes['per_app_modes'][self.data.application['name']][priority['name']] = 'drop';
          })
          self.data.unsubscribeButton.prop('disabled', true);
          $.ajax({
              url: '/v0/users/modes/' + window.appData.user,
              data: JSON.stringify(modes),
              method: 'POST',
              contentType: 'application/json'
          }).done(function(r) {
            iris.createAlert('Successfully unsubscribed from all messages sent by this app!', 'success')
          }).fail(function(r) {
            iris.createAlert('Failed to unsubscribe: ' + r.responseJSON['title'])
          }).always(function(){
            self.data.unsubscribeButton.prop('disabled', false);
          })
        }
      },
      // Needed for single stats routing
      singlestats: {},
      singlestat: {
        data: {
          url: '/v0/singlestats/',
          $page: $('.stats'),
          $table: $('#stats-table'),
          tableTemplate: $('#stats-table-template').html(),
          DataTable: null,
          statName: null,
          dataTableOpts: {
            orderClasses: false,
            order: [[0, 'asc']],
            columns: [
              null,
              null
            ]
          }
        },
        init: function() {
          var location = window.location.pathname.split('/'),
              statName = decodeURIComponent(location[location.length - 1]);
          this.data.statName = statName;

          $('#stats-header').text("Stats: " + statName);
          iris.tables.filterTable.call(this);
        },
        events: function() {},
        getData: function(params) {
          dataUrl = this.data.url + this.data.statName;
          return $.getJSON(dataUrl).fail(function(){
            iris.createAlert('No stats found');
          });
        }
      }, // End iris.hpistats
      tables: {
        filterTable: function(e){
          if (e) {
            // form submitted - serialize and shove into qs
            var $form = $(e.target);
            var $btn;
            $btn = $form.find('button[type="submit"]');
            $btn.prop('disabled', true);
            e.preventDefault();

            var url = window.location.protocol + "//" + window.location.host + window.location.pathname + '?';
            var qs_form = $form.serializeArray();
            for (var i = 0; i < qs_form.length; i++) {
              var k = qs_form[i].name;
              var v = qs_form[i].value;
              if (v) {
                url += k.slice(7) +'=' + encodeURI(v) + '&';
              }
            }
            url = url.slice(0, -1);
            history.pushState(url, null, url);
          }
          var self = this;

          if (window.location.search) {
            var qs = {};
            var qs_parts = decodeURI(window.location.search.substr(1)).split('&');
            for (i = qs_parts.length - 1; i >= 0; i--) {
              var qs_pair = qs_parts[i].split('=');
              qs[qs_pair[0]] = qs_pair[1];
            }
          } else {
            qs = {
              'active': 'active',
              'target': appData.user,
              // Default incident start time to now() - 1 day
              'incidentStart': moment(Date.now() - 86400000).format('MM/DD/YYYY h:mm A')
            };
          }
          var params = {};

          // add loading icon
          this.data.$table.html('<tr><td><i class="loader"></i></td></tr>');
          $('#filter-form input, #filter-form select').each(function(){

            var $this = $(this);
            var name = $this.attr('name');
            if (typeof(name) != 'undefined') {
              var qs_name = name.split('-')[1];
              var qs_value = qs[qs_name];
            }

            switch (name) {
              case 'filter-active':
                var v = $this.prop('id').slice(7);
                if ((v == qs_value) || (v=='all' && qs_value === undefined)) {
                  $this.prop('checked', true);
                } else {
                  $this.prop('checked', false);
                }
                break;
              case 'filter-incidentStart':
              case 'filter-start':
              case 'filter-end':
                $this.val(qs_value);
                if ($this.val().length) {
                  params[$this.attr('data-param')] = moment(qs_value).unix();
                }
                break;
              case 'filter-target':
                $this.typeahead('val', qs_value);
                params[$this.attr('data-param')] = qs_value;
                break;
              default:
                $this.val(qs_value);
                params[$this.attr('data-param')] = qs_value;
                break;
            }

          });

          switch (qs['active']) {
            case 'active':
              params['active'] = 1;
              break;
            case 'inactive':
              params['active'] = 0;
              break;
          }

          self.getData(params).done(function(data){
            if (self.data.DataTable) {
              self.data.DataTable.destroy();
            }
            self.data.$table.empty();
            iris.tables.createTable.call(self, data);
          }).always(function(){
            if ($btn && $btn.prop('disabled')) { $btn.prop('disabled', false) }
          });
        },
        createTable: function(data){
          var template = Handlebars.compile(this.data.tableTemplate),
              options = this.data.dataTableOpts || { orderClasses: false };
          if (data.length == iris.data.tableEntryLimit){
            data.limit = iris.data.tableEntryLimit;
          }
          this.data.$table.html(template(data));
          this.data.DataTable = this.data.$table.DataTable(options);
          iris.tables.bindArrowKeys(this.data.DataTable);
          iris.tables.bindUrlPagination(this.data.DataTable);
        },
        bindArrowKeys: function(dataTable) {
          $(document).keydown(function(e) {

            if (document.activeElement && (document.activeElement.nodeName === 'INPUT'
                                          || document.activeElement.nodeName === 'TEXTAREA')) {
              return;
            }

            if (e.keyCode == 37) {
              dataTable.page('previous').draw(false);
            } else if (e.keyCode == 39) {
              dataTable.page('next').draw(false);
            }
          });
        },
        bindUrlPagination: function(dataTable) {
          // If we currently have a page number in URL, use it
          var parts = window.location.hash.split('-');
          if (parts.length == 2 && (parts[1] - 1) < dataTable.page.info().pages) {
              dataTable.page(parts[1] - 1).draw(false);
          }

          // Store page number in URL for future refreshes / back buttons
          dataTable.on('page.dt', function() {
            var current_page = dataTable.page.info().page + 1;
            window.history.replaceState(undefined, undefined, '#page-' + current_page)
          });
        }
      },
      createAlert: function(alertText, type, $el, action, fixed){
        //params:
        //-- alertText: content of alert *REQUIRED* --string--
        //-- type: type of alert (coincides to color) --string--
          //---- 'danger' - red *default*
          //---- 'warning' - yellow
          //---- 'info' - blue
          //---- 'success' - green
        //-- $el: DOM element which the alert will be added to. Defaults to body --jQuery element--
        //-- action: jQuery action on the $el.
          //---- 'prepend' - inserts alert as first element inside $el *default*
          //---- 'append' - inserts alert at the end of the $el
          //---- 'before' - inserts alert as a sibling node before $el
          //---- 'after' - inserts alert as a sibling node after $el
        //-- fixed: alternate alert which is absolutely positioned at top center of the screen
        var alert;
        type = type || 'danger';
        $el = $el || $('.main');
        action = action || 'prepend';
        $('#iris-alert').remove();
        alert = '<div id="iris-alert" class="alert alert-'+ type +' alert-dismissible ' + fixed + '" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><span class="alert-content"></span></div>';
        $el[action](alert);
        $('#iris-alert .alert-content').html(alertText);
      }, //end createAlert
      dismissAlerts: function() {
        $('#iris-alert').remove();
      },
      typeahead: {
        data: {
          targetUrl: '/v0/targets/',
          planUrl: '/v0/plans?name__startswith=%QUERY&active=1',
          field: 'input.typeahead'
        },
        init: function(urlType){
          var $field = $(this.data.field),
              self = this;
          $field.typeahead('destroy').each(function(){
            var $this = $(this),
                type = $this.data('targettype') || (urlType != undefined ? urlType : $this.parents('.plan-notification').find('select[data-type="role"] option:selected').attr('data-url-type')), //get url type from sibling "Role" option
                itemType = $this.data('typeaheadtype'),
                results = new Bloodhound({
                  datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
                  queryTokenizer: Bloodhound.tokenizers.whitespace,
                  remote: {
                    url: itemType == 'plan' ? self.data.planUrl : self.data.targetUrl + type + '?startswith=%QUERY&active=1',
                    wildcard: '%QUERY',
                    transform: function(response) {
                      if (itemType == 'plan') {
                        var names = [];
                        response.forEach(function(plan) {
                          names.push(plan.name);
                        });
                        return names;
                      } else {
                        return response;
                      }
                    }
                  }
                });
            $this.typeahead(null, {
              hint: true,
              async: true,
              highlight: true,
              source: results
            }).on('typeahead:select', function(){
              $(this).attr('value', $(this).val());
            });
          });
        },
        destroy: function() {
          $(this.data.field).typeahead('destroy');
        }
      },
      unloadDialog: function(){
        if ( this.data.$page.find('input, textarea').not('[data-default]').not('[disabled]').not('.unload-exclude').filter(function () { return !!this.value }).length > 0 ) {
          return 'You have unsaved changes';
        }
      },
      versionTour: {
        type: 'templates',
        init: function(type){
          var self = this;
          this.type = type;
          if (!localStorage.getItem('tourCompleted')) {
            hopscotch.startTour(self);
          }
          $('.main').on('click', '.start-tour', function(){
            hopscotch.startTour(self);
          });
        },
        id: "version-tour",
        steps: [
          {
            title: "Changes to versioning",
            content: "Plans or templates with the same name are now combined into one view. You can click this dropdown to select older versions of this plan or template.",
            target: ".version-select",
            placement: "bottom",
            xOffset: -90,
            arrowOffset: 'center'
          },
          {
            title: "Activate old plans or templates",
            content: "If a plan or template is deactivated, you can click here to set it as active. This will deactivate all other plans or templates with this name.",
            target: ".badge",
            placement: "bottom"
          },
          {
            title: "Related plans",
            content: "You can click here to see all plans that are currently using this template. It may be a good idea to review the related plans before activating an older version of a template (it's possible someone else's plan is using your template, and you don't want to ruin their plan!)",
            target: ".view-related",
            placement: "bottom"
          },
          {
            title: "Learn about versioning",
            content: "Click this button to restart this tutorial if you need a reminder.",
            target: ".start-tour",
            placement: "bottom",
            xOffset: -20
          }
        ],
        onEnd: function(){
          iris.versionTour.saveState();
        },
        onClose: function(){
          iris.versionTour.saveState();
        },
        saveState: function(){
          localStorage.setItem('tourCompleted', true);
        },
        showPrevButton: true
      },
      registerHandlebarHelpers: function(){
        // Register handlebars helpers
        Handlebars.registerHelper('ifNot', function(val, opts){
          return val ? opts.inverse(this) : opts.fn(this);
        });
        Handlebars.registerHelper('ifIn', function(needle, haystack, opts){
          if (Array.isArray(haystack)) {
            return haystack.indexOf(needle) != -1 ? opts.fn(this) : opts.inverse(this);
          } else {
            return needle in haystack;
          }
        });
        Handlebars.registerHelper('hasKeys', function(val, opts){
          return Object.keys(val).length ? opts.fn(this) : opts.inverse(this);
        });
        Handlebars.registerHelper('isSelected', function(val, check){
          return val === check ? 'selected': '';
        });
        Handlebars.registerHelper('isActive', function(yes){
          return yes ? 'active': '';
        });
        Handlebars.registerHelper('ifExists', function(val, opts){
          return typeof(val) !== 'undefined' ? opts.fn(this) : opts.inverse(this);
        });
        Handlebars.registerHelper('isEqual', function(val1, val2, opts){
          return val1 === val2 ? opts.fn(this) : opts.inverse(this);
        });
        Handlebars.registerHelper('isUser', function(val1, opts){
          return val1 === window.appData.user ? opts.fn(this) : opts.inverse(this);
        });
        Handlebars.registerHelper('divide', function(val1, val2){
          return val1 / val2;
        });
        Handlebars.registerHelper('add', function(val1, val2){
          return val1 + val2;
        });
        Handlebars.registerHelper('markdown', function(val){
          return new Handlebars.SafeString(marked(val, {sanitize: true}));
        })
        Handlebars.registerHelper('prettyPrint', function(val){
          return typeof(val) === 'string' ? val : "{...}";
        });
        Handlebars.registerHelper('eachInSet', function(context, options) {
            // handle sets and return them in sorted order
            var ret = "";
            values = Array.from(context).sort();
            values.forEach(function(val) {
                ret = ret + options.fn({value:val});
            });
            return ret;
        });
        Handlebars.registerHelper('secondsToMinutes', function(val){
          if (val) {
            return parseFloat((val / 60).toFixed(2));
          } else {
            return 0;
          }
        });
        Handlebars.registerHelper('convertToLocal', function(time){
          if (time) {
            if (window.appData.user_settings.timezone) {
              return moment.unix(time).tz(window.appData.user_settings.timezone).toString();
            } else {
              return moment.unix(time).local().toString();
            }
          }
        });
        Handlebars.registerHelper('breakLines', function(text, type){
          if (text) {
            text = Handlebars.Utils.escapeExpression(text);
            if (type && type === 'input') {
              text = text.replace(/(\r\n|\n|\r)/gm, '&#13;&#10;');
            } else {
              text = text.replace(/(\r\n|\n|\r)/gm, '<br />');
            }

            return new Handlebars.SafeString(text);
          } else {
            return '';
          }
        });
        Handlebars.registerHelper('getValForKey', function (obj, val1, val2, breakLines) {
          //gets nested value from an object with a dynamic key.
          //obj = object to get val from
          //val1 = key to get val from
          //val2 = key within val1 to get the value from
          //breakLines = replaces \n with <br /> tag for view mode of templates
          var text = obj[val1][val2];
          if (breakLines === true) {
            text = Handlebars.helpers.breakLines(text);
          } else {
            text = Handlebars.Utils.escapeExpression(text);
            text = text.replace(/(\r\n|\n|\r)/gm, '&#13;&#10;');
          }
          return new Handlebars.SafeString(text);
        });
        Handlebars.registerHelper('trim', function(string, start, end) {
          if (string) {
            return string.slice(start, end);
          } else {
            return string
          }
        });
        Handlebars.registerHelper('unixToDate', function(val){
          if (val) {
            var a = new Date(val * 1000);
            var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
            var year = a.getFullYear();
            var month = months[a.getMonth()];
            var date = a.getDate();
            var hour = a.getHours();
            if(hour < 10){hour = '0' + hour}
            var min = a.getMinutes();
            if(min < 10){min = '0' + min}
            var sec = a.getSeconds();
            if(sec < 10){sec = '0' + sec}
            var time = date + ' ' + month + ' ' + year + ' ' + hour + ':' + min + ':' + sec ;
            return time;
          } else {
            return "N/A";
          }
        });
        Handlebars.registerHelper('range', function(n, block) {
          var accum = '';
          for (var i = 0; i < n; i++) {
            accum += block.fn(i);
          }
          return accum;
        });
        Handlebars.registerHelper('regex', function (val, regex) {
          return (new RegExp(regex).test(val))
        })
      } //end registerHandlebarHelpers
    }; //end iris

    iris.init();
