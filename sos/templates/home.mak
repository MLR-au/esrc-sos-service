<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="eScholarship Research Centre Single Sign on Service"
    <meta name="author" content="Dr Marco La Rosa <m@lr.id.au>">

    <meta http-equiv="cache-control" content="max-age=0" />
    <meta http-equiv="cache-control" content="no-cache" />
    <meta http-equiv="expires" content="0" />
    <meta http-equiv="expires" content="Tue, 01 Jan 1980 1:00:00 GMT" />
    <meta http-equiv="pragma" content="no-cache" />

    <title>eSRC Sign on Service (SOS)</title>

    <!-- Bootstrap core CSS -->
    <link href="/static/bootstrap.min.css" rel="stylesheet">
    <script src="/static/jquery.min.js"></script>
    <script src="/static/spin.min.js"></script>

    <script>

        $(document).ready(function() {
            $('#loadingIndicator').hide();
            var opts = {
              lines: 13, // The number of lines to draw
              length: 20, // The length of each line
              width: 5, // The line thickness
              radius: 10, // The radius of the inner circle
              corners: 1, // Corner roundness (0..1)
              rotate: 0, // The rotation offset
              direction: 1, // 1: clockwise, -1: counterclockwise
              color: '#000', // #rgb or #rrggbb or array of colors
              speed: 1, // Rounds per second
              trail: 60, // Afterglow percentage
              shadow: false, // Whether to render a shadow
              hwaccel: false, // Whether to use hardware acceleration
              className: 'spinner', // The CSS class to assign to the spinner
              zIndex: 2e9, // The z-index (defaults to 2000000000)
              top: '140px', // Top position relative to parent
              left: '50%' // Left position relative to parent
            };

            $('.btn').click(function() {
                $('#loginForms').hide();
                $('#loadingIndicator').show();
                var target = document.getElementById('spinner');
                var spinner = new Spinner(opts).spin(target);
            });
        });
        
    </script>
    <style>
        body {
            background-color: #efefea;
        }
    </style>
  </head>

  <body>
    <div class="row" style="background-color: #003268; height: 20px;">
    </div>
    <div class="container">
        <div class="row">
            <div class="col-sm-12 col-md-12 col-lg-12 text-center">
                <h3 style="text-shadow: 1px -1px 2px #595959; color: #658095; line-height: 1.1;">
                    <span style="color: #3d4343;">eScholarship Research Centre</span>
                </h3>
                <h2 style="text-shadow: 1px -1px 2px #595959; color: #658095; line-height: 1.1;">
                    <span style="color: #3d4343;">Sign on Service</span>
                </h2>
            </div>
        </div>
        <hr style="border-color: #003268;" />
        <div class="row">
            <div class="col-sm-12 col-md-12 col-lg-12 text-center">
                %if r != '':
                    <p>You came from: <a href="${r}">${r}</a></p>
                %endif
                %if e == 'True':
                    <div class="alert alert-danger small">Sorry - we couldn't log you in. Please try again.</div>
                %endif
            </div>
        </div>
        <hr style="border-color: #003268;" />
        <div class="row" style="border: 2px solid grey; border-radius: 8px; margin: 1px;">
            <div class="col-sm-6 col-md-6 col-lg-6" id="loadingIndicator">
                <div id="spinner"></div>
                <p class="text-center">Logging you in. Just a moment...</p>
            </div>
            <div class="col-sm-6 col-md-6 col-lg-6" id="loginForms">
                <h4 class="text-center">Login</h4>
                <form role="form" action="/login/staff" method="POST">
                    <input type="hidden" name="r" value="${r}" >
                    <div class="form-group">
                        <input type="username" name="username" class="form-control" placeholder="Enter your eSRC username" required autofocus>
                    </div>
                    <div class="form-group">
                        <input type="password" name="password" class="form-control" placeholder="Password" required>
                    </div>
                    <button class="btn btn-default btn-block">Login</button>
                </form>
                <hr style="border-color: #003268;"/>
                <h5 class="text-center">OR</h5>
                <hr style="border-color: #003268;"/>

                <form role="form" action="/login/google" method="POST">
                    <button class="btn btn-default btn-block" type="submit">
                        <img src="/static/img/google.jpg" style="height: 20px;"/>&nbsp;Login with your Google account
                    </button>
                </form>
                <br/>
                <form role="form" action="/login/linkedin" method="POST">
                    <button class="btn btn-default btn-block" type="submit">
                        <img src="/static/img/linkedin.png" style="height: 20px;"/>&nbsp;Login with your LinkedIn account
                    </button>
                </form>
                <br/>
            </div>
            <div class="col-sm-6 col-md-6 col-lg-6">
                <h4 class="text-center">Help</h4>
                <p class="">Staff should login using their eSRC user account and password. Some collaborators will
                also have a systems account and you should use this if you do.</p>
                <hr/>
                <p class="">Collaborators who don't have an eSRC account should use one of the supported external 
                authentication providers noting that this will not automatically grant access. A staff member needs to have
                granted you access before you can login to an application.
                </p>
            </div>
        </div>
        <hr/>
        <div class="row">
            <div class="col-sm-12 col-md-12 col-lg-12 alert alert-info">
                <h5>Why am I here?</h5>
                <p class="">The eScholarship Research Centre operates a number services on behalf of staff and collaborators. In order to
                provide a unified experience across those services, a central sign on service (this site) has been 
                developed. If you try to access an eSRC service and end up here you can confirm that this is the expected behaviour
                by checking that the site you came from is shown at the top of the page.</p>
                <p class="">After you've logged in successfully you will automatically be redirected to the service you came from so that you
                can continue with your work.</p>
            </div>
        </div>

    </div>
  </body>
</html>
