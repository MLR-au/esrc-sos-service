<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="pyramid web application">
    <meta name="author" content="Pylons Project">
    <link rel="shortcut icon" href="${request.static_url('essos:static/pyramid-16x16.png')}">

    <title>Starter Scaffold for The Pyramid Web Framework</title>

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
        <hr/>
        <div class="row">
            <div class="col-sm-12 col-md-12 col-lg-12 text-center">
                <p>You came from: <a href="https://ohrm.esrc.info">https://ohrm.esrc.info</a></p>
            </div>
        </div>
        <hr/>
        <div class="row" style="border: 2px solid grey; border-radius: 8px;">
            <div class="col-sm-6 col-md-6 col-lg-6" style="border-right: 1px solid grey;">
                <h4 class="text-center">Staff</h4>
                <hr/>
                <form role="form">
                    <div class="form-group">
                        <input type="username" class="form-control" placeholder="Enter your eSRC username">
                    </div>
                    <div class="form-group">
                        <input type="password" class="form-control" placeholder="Password">
                    </div>
                </form>
                <p class="text-muted">Staff should login using their eSRC user account and password.</p>
            </div>
            <div class="col-sm-6 col-md-6 col-lg-6">
                <h4 class="text-center">Collaborators</h4>
                <hr/>
                <p class="text-muted">Please login with one of the supported external authentication providers. Note
                that this will not automatically grant you access if this is your first time here. 
                </p>
                <p class="text-muted">If you require access to
                one of our services an eSRC staff member will authorise your account and grant privileges as appropriate.
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
