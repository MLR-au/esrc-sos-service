'use strict';

angular.module('adminApp')
  .constant('configuration', {
      'development': 'http://dev01.internal:3000',
      'testing': '',
      'production': '',
      'service': 'development'
  });
