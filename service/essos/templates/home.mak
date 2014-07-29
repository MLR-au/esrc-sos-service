<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="pyramid web application">
    <meta name="author" content="Pylons Project">
    <link rel="shortcut icon" href="${request.static_url('essos:static/pyramid-16x16.png')}">

    <title>eSRC Single Sign on Service (ESSOS)</title>

    <!-- Bootstrap core CSS -->
    <link href="/static/bootstrap.min.css" rel="stylesheet">

  </head>

  <body>
    <div class="container">
        <div class="row">
            <div class="col-sm-12 col-md-12 col-lg-12 text-center">
                <h3><a href="http://www.esrc.unimelb.edu.au" target="_blank">eScholarship Research Centre</a></h3>
                <h4>Single Sign on Service</h4>
            </div>
        </div>
        <div class="row">
            <div class="col-sm-12 col-md-12 col-lg-12 text-center">
                %if r != '':
                    <hr/>
                    <p>You came from: <a href="${r}">${r}</a></p>
                %endif
                %if e == 'True':
                    <div class="alert alert-danger small">Sorry - we couldn't log you in. Please try again.</div>
                %endif
            </div>
        </div>
        <hr/>
        <div class="row" style="border: 2px solid grey; border-radius: 8px; margin: 1px;">
            <div class="col-sm-6 col-md-6 col-lg-6">
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
                <hr/>
                <h5 class="text-center">OR</h5>
                <hr/>

                <form role="form" action="/login/google" method="POST">
                    <input type="hidden" name="r" value="${r}" >
                    <button class="btn btn-default btn-block" type="submit">
                        <img src="/static/img/google.jpg" style="height: 20px;"/>&nbsp;Login with your Google account
                    </button>
                </form>
                <br/>
                <form role="form" action="/login/linkedin" method="POST">
                    <input type="hidden" name="r" value="${r}" >
                    <button class="btn btn-default btn-block" type="submit">
                        <img src="/static/img/linkedin.png" style="height: 20px;"/>&nbsp;Login with your LinkedIn account
                    </button>
                </form>
                <br/>
            </div>
            <div class="col-sm-6 col-md-6 col-lg-6">
                <h4 class="text-center">Help</h4>
                <p class="text-muted">Staff should login using their eSRC user account and password. Some collaborators will
                also have a systems account and you should use this if you do.</p>
                <hr/>
                <p class="text-muted">Collaborators who don't have an eSRC account should use one of the supported external 
                authentication providers noting that this will not automatically grant access. After logging in for the first
                time an eSRC staff member will authorise your account and grant you access to the
                resources you require.
                </p>
            </div>
        </div>
        <hr/>
        <div class="row">
            <div class="col-sm-12 col-md-12 col-lg-12">
                <h5>Why are you here?</h5>
                <p class="text-muted">The eScholarship Research Centre operates a number services on behalf of staff and collaborators. In order to
                provide a unified experience across those services, a central single sign on service (this site) has been 
                developed. If you try to access an eSRC service and end up here you can confirm that this is the expected behaviour
                by checking that the site you came from is shown at the top of the page.</p>
                <p class="text-muted">After you've logged in successfully you will automatically be redirected to the service you came from so that you
                can continue with your work.</p>
            </div>
        </div>

    </div>
  </body>
</html>
