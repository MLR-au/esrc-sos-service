'use strict';

angular.module('adminApp')
  .service('AuthService', [ '$location', '$http', function AuthService($location, $http) {

      var debug = true;
      var log = function(msg) {
          if (debug) {
              console.log(msg);
          }
      }
      
      /* 
       * @function: init
       */
      function init(authService) {
          log('init method called');
          var l = {};
          angular.copy($location.search(), l);
          AuthService.service = authService;

          if (angular.isUndefined(l.s)) {
              // if there's no code; redirect to essos so the user can log in
              log('No code defined; calling login method');
              AuthService.login();
          } else {
              log('Code found in url');
              // there is a code
              AuthService.code = l.s;

              // use the ONE TIME CODE to GET the token
              log('Retrieving token');
              var url = AuthService.service + '/code/' + AuthService.code + '?callback=JSON_CALLBACK';
              $http.jsonp(url).then(function(resp) {
                  log('Token retrieved');
                  AuthService.token = resp.data.token;
                  log('User logged in!', AuthService.token);

                  // we received a token so populate the user data
                  log('Retrieving user data');
                  AuthService.getUserData();
              },
              function(resp) {
                  // Most likely a 401 unauthorised 
                  log('401 raised; calling login method');
                  AuthService.login();
              });
          }
      }

      /*
       * @function: login
       */
      function login() {
          log('login method called');
          $location.search('');
          var redirectTo = AuthService.service + '/?r=' + encodeURIComponent($location.absUrl());
          window.location = redirectTo;
      }

      /*
       * @function: logout
       */
      function logout() {
          var url = AuthService.service + '/logout?callback=JSON_CALLBACK';
          $http.jsonp(url).then(function(resp) {
              AuthService.login();
          },
          function(resp) {
          });
      }

      /*
       * @function: getUserData
       */
      function getUserData() {
          log('getUserData method called');
          var url = AuthService.service + '/token';
          var config = {
              'url': url,
              'method': 'POST',
              'data': {
                  'token': AuthService.token,
              },
          };
          $http.post(url, config).then(function(resp) {
              log('Retrieved user data');
              AuthService.userData = angular.fromJson(resp.data);
              log(AuthService.userData);
          },
          function(resp) {
              // Most likely a 401 unauthorised
              log('401 raised; calling login method');
              AuthService.login();
          });
      }


      var AuthService = {
          service: undefined,
          token: undefined,
          init: init,
          login: login,
          logout: logout,
          getUserData: getUserData
      };
      return AuthService;

  }]);
