from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category, Page
from rango.forms import CategoryForm
from django.shortcuts import redirect
from django.urls import reverse
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from datetime import datetime
from rango.search import run_query   
from django.views import View
from django.utils.decorators import method_decorator
    

def index(request):
    context_dict = {'aboldmessage': 'Crunchy, creamy, cookie, candy, cupcake!'}
    # Query the database for a list of ALL categories currently stored.
    # Order the categories by the number of likes in descending order.
    # Retrieve the top 5 only -- or all if less than 5.
    category_list = Category.objects.order_by('-likes')[:5]
    # Place the list in our context_dict dictionary (with our boldmessage!)
    # that will be passed to the template engine.
    context_dict['categories'] = category_list
    # Query the database for a list of pages
    # Order the pages by the number of views in descending order
    # retrieve the top 5 pages
    page_list = Page.objects.order_by('-views')[:5]
    context_dict['pages'] = page_list
    context_dict['extra'] = 'From the model solution on GitHub'
    # Client side cookies
    #context_dict['visits'] = int(request.COOKIES.get('visits', '1'))
    # Server side cookies
    context_dict['visits'] = get_server_side_cookie(request, 'visits', 1)
    # request.session.set_test_cookie()
    # Obtain our Response object early so we can add cookie information.
    # Side server side cookie function
    visitor_cookie_handler(request)
    
    response = render(request, 'rango/index.html', context=context_dict)
 
    # Call the helper function to handle the cookies
    # Client side cookie function
    # response = visitor_cookie_handler(request, response)
    
    
    # Return response back to the user, updating any cookies that need changed.
    return response

    #context_dict = {'aboldmessage': 'Crunchy, creamy, cookie, candy, cupcake!'}
    #return HttpResponse("Rango says hey there partner! <a href='/rango/about/'>About</a>")
    #return render(request, 'rango/index.html', context=context_dict)


def about(request):
    #return HttpResponse("Rango says here is the about page. <a href='/rango/'>Index</a>")
    #if request.session.test_cookie_worked():
    #    print("TEST COOKIE WORKED!")
    #    request.session.delete_test_cookie()
    
    return render(request, 'rango/about.html', context={})


def show_category(request, category_name_slug):
    # Create a context dictionary which we can pass
    # to the template rendering engine.
    context_dict = {}

    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # The .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)

        # Retrieve all of the associated pages.
        # The filter() will return a list of page objects or an empty list.
        pages = Page.objects.filter(category=category).order_by('-views')

        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from
        # the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything -
        # the template will display the "no category" message for us.
        context_dict['category'] = None
        context_dict['pages'] = None
    
    # Start new search functionality code.
    context_dict['query'] = 'search'
    if request.method == 'POST':
        query = request.POST['query'].strip()
            
        if query:
            context_dict['result_list'] = run_query(query)
            context_dict['query'] = query
	# End new search functionality code.

    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context=context_dict)


def add_category(request):
    form = CategoryForm()

    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)
            # Now that the category is saved, we could confirm this.
            # For now, just redirect the user back to the index view.
            return redirect('/rango/')
        else:
            # The supplied form contained errors -
            # just print them to the terminal.
            print(form.errors)

    # Will handle the bad form, new form, or no form supplied cases.
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})


def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    # You cannot add a page to a Category that does not exist...
    if category is None:
        return redirect(reverse('rango:index'))

    form = PageForm()

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()

                return redirect(reverse('rango:show_category',
                                        kwargs={'category_name_slug':
                                                    category_name_slug}))
        else:
            print(form.errors)

    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context=context_dict)

def register(request):
    # A boolean value for telling the template 
    # whether the registration was successful.
    # Set to False initially. Code changes value to 
    # True when registration succeeds.
    registered = False
    
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.	
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()
            
            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()
            
            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, 
            # we set commit=False. This delays saving the model 
            # until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user
            
            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and 
            #put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            
            # Now we save the UserProfile model instance.
            profile.save()
            
            # Update our variable to indicate that the template
            # registration was successful.
            registered = True
        else:
            # Invalid form or forms - mistakes or something else?
            # Print problems to the terminal.
            print(user_form.errors, profile_form.errors)
    else:
        # Not a HTTP POST, so we render our form using two ModelForm instances.
        # These forms will be blank, ready for user input.
        user_form = UserForm()
        profile_form = UserProfileForm()
    
    # Render the template depending on the context.
    return render(request,
                    'rango/register.html',
                    context = {'user_form': user_form,
                                'profile_form': profile_form, 
                                'registered': registered})


def user_login(request):
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        # We use request.POST.get('<variable>') as opposed
        # to request.POST['<variable>'], because the
        # request.POST.get('<variable>') returns None if the
        # value does not exist, while request.POST['<variable>']
        # will raise a KeyError exception.
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)
        
        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return redirect(reverse('rango:index'))
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print(f"Invalid login details: {username}, {password}")
            return HttpResponse("Invalid login details supplied.")
        
    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'rango/login.html')
    
def some_view(request):
    if not request.user.is_authenticated():
        return HttpResponse("You are logged in.")
    else:
        return HttpResponse("You are not logged in.")
    
@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")

@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    # Take the user back to the homepage.
    return redirect(reverse('rango:index'))

#   Function for cookies on the client side
#
#def visitor_cookie_handler(request, response):
#    # Get the number of visits to the site.
#    # We use the COOKIES.get() function to obtain the visits cookie.
#    # If the cookie exists, the value returned is casted to an integer.
#    # If the cookie doesn't exist, then the default value of 1 is used.
#    visits = int(request.COOKIES.get('visits', '1'))
#    last_visit_cookie = request.COOKIES.get('last_visit', str(datetime.now()))
#    last_visit_time = datetime.strptime(last_visit_cookie[:-7],'%Y-%m-%d %H:%M:%S')
#        
#    # If it's been more than a day since the last visit...
#    if (datetime.now() - last_visit_time).seconds > 0:
#        visits = visits + 1
#        # Update the last visit cookie now that we have updated the count
#        response.set_cookie('last_visit', str(datetime.now()))
#    else:
#        # Set the last visit cookie
#        response.set_cookie('last_visit', last_visit_cookie)
#    # Update/set the visits cookie
#    response.set_cookie('visits', visits)
#    return response



def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val
	
# Updated the function for cookies server side
def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))
    last_visit_cookie = get_server_side_cookie(request,'last_visit',str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')
	
    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).seconds > 0:
        visits = visits + 1
        # Update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:
        # Set the last visit cookie 
        request.session['last_visit'] = last_visit_cookie
	    
    # Update/set the visits cookie
    request.session['visits'] = visits
 



#def search(request):
#    result_list = []
#    if request.method == 'POST':
#        query = request.POST['query'].strip()
#        if query:
#	        # Run our Bing function to get the results list!
#	        result_list = run_query(query)
#    return render(request, 'rango/search.html', {'result_list': result_list})


def goto_url(request):
    if request.method == 'GET':
        page_id = request.GET.get('page_id')
        try:
            selected_page = Page.objects.get(id=page_id)
            selected_page.views = selected_page.views + 1
            selected_page.save()
            return redirect(selected_page.url)
        except Page.DoesNotExist:
            return redirect(reverse('rango:index'))
    return redirect(reverse('rango:index'))


@login_required
def register_profile(request):
    form = UserProfileForm()
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            
            return redirect(reverse('rango:index'))
        else:
            print(form.errors)
    
    context_dict = {'form': form}
    return render(request, 'rango/profile_registration.html', context_dict)



from registration.backends.simple.views import RegistrationView

class MyRegistrationView(RegistrationView):
    def get_success_url(self, user):
        return reverse('rango:register_profile')
    
from django.views import View    

class AboutView(View):
    def get(self, request):
        context_dict = {}
        visitor_cookie_handler(request)
        context_dict['visits'] = request.session['visits']
        return render(request, 'rango/about.html',  context_dict)
 
        
from django.utils.decorators import method_decorator       

class AddCategoryView(View):
    @method_decorator(login_required)
    def get(self, request):
        form = CategoryForm()
        return render(request, 'rango/add_category.html', {'form': form})
    
    @method_decorator(login_required)
    def post(self, request):
        form = CategoryForm(request.POST)
        
        if form.is_valid():
            form.save(commit=True)
            return redirect(reverse('rango:index'))
        else:
            print(form.errors)
        
        return render(request, 'rango/add_category.html', {'form': form})
    
    
class ShowCategoryView(View):
    def get(self, request, category_name_slug):
        context_dict = self.gather_category_data(context_dict={}, category_name_slug=category_name_slug)
        return render(request, 'rango/category.html', context=context_dict)   
    
    def post(self, request, category_name_slug):
        context_dict = self.gather_category_data(context_dict={}, category_name_slug=category_name_slug)
        query = request.POST['query'].strip()
        if query:
            context_dict['result_list'] = run_query(query)
            context_dict['query'] = query
        return render(request, 'rango/category.html', context=context_dict)   

    
    def gather_category_data(self, context_dict, category_name_slug):
        try:
            # Can we find a category name slug with the given name?
            # If we can't, the .get() method raises a DoesNotExist exception.
            # The .get() method returns one model instance or raises an exception.
            category = Category.objects.get(slug=category_name_slug)

            # Retrieve all of the associated pages.
            # The filter() will return a list of page objects or an empty list.
            pages = Page.objects.filter(category=category).order_by('-views')

            # Adds our results list to the template context under name pages.
            context_dict['pages'] = pages
            # We also add the category object from
            # the database to the context dictionary.
            # We'll use this in the template to verify that the category exists.
            context_dict['category'] = category
        except Category.DoesNotExist:
            # We get here if we didn't find the specified category.
            # Don't do anything -
            # the template will display the "no category" message for us.
            context_dict['category'] = None
            context_dict['pages'] = None
        return context_dict    
    

class IndexView(View): 
    def get(self, request):
        context_dict = {'aboldmessage': 'Crunchy, creamy, cookie, candy, cupcake!'}
        category_list = Category.objects.order_by('-likes')[:5]
        context_dict['categories'] = category_list
        page_list = Page.objects.order_by('-views')[:5]
        context_dict['pages'] = page_list
        context_dict['extra'] = 'From the model solution on GitHub'
        context_dict['visits'] = get_server_side_cookie(request, 'visits', 1)
        visitor_cookie_handler(request)
        response = render(request, 'rango/index.html', context=context_dict)
        return response

from django.contrib.auth.models import User
from rango.models import UserProfile

class ProfileView(View):
    def get_user_details(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        
        user_profile = UserProfile.objects.get_or_create(user=user)[0]
        form = UserProfileForm({'website': user_profile.website,
                                'picture': user_profile.picture})
        
        return (user, user_profile, form)
    
    @method_decorator(login_required)
    def get(self, request, username):
        try:
            (user, user_profile, form) = self.get_user_details(username)
        except TypeError:
            return redirect(reverse('rango:index'))
        
        context_dict = {'user_profile': user_profile,
                        'selected_user': user,
                        'form': form}
        
        return render(request, 'rango/profile.html', context_dict)
    
    @method_decorator(login_required)
    def post(self, request, username):
        try:
            (user, user_profile, form) = self.get_user_details(username)
        except TypeError:
            return redirect(reverse('rango:index'))
        
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        if form.is_valid():
            form.save(commit=True)
            return redirect('rango:profile', user.username)
        else:
            print(form.errors)
        
        context_dict = {'user_profile': user_profile,
                        'selected_user': user,
                        'form': form}
        
        return render(request, 'rango/profile.html', context_dict)
    
    
    
class ListProfilesView(View):
    @method_decorator(login_required)
    def get(self, request):
        profiles = UserProfile.objects.all()
        
        return render(request,
                        'rango/list_profiles.html',
                        {'userprofile_list': profiles})
        
class LikeCategoryView(View):
    @method_decorator(login_required)
    def get(self, request):
        category_id = request.GET['category_id']
        try:
            category = Category.objects.get(id=int(category_id))
        except Category.DoesNotExist:
            return HttpResponse(-1)
        except ValueError:
            return HttpResponse(-1)
        category.likes = category.likes + 1
        category.save()
        return HttpResponse(category.likes)
    

def get_category_list(starts_with='', max_results=0):
    category_list = []
    if starts_with:
        category_list = Category.objects.filter(name__istartswith=starts_with)
    
    if max_results > 0:
        if len(category_list) > max_results:
            category_list = category_list[:max_results]
    
    return category_list


class CategorySuggestionView(View):
    def get(self, request):
        if 'suggestion' in request.GET:
            suggestion = request.GET['suggestion']
        else:
            suggestion = ''
        
        category_list = get_category_list(max_results=8,
        starts_with=suggestion)
        
        if len(category_list) == 0:
            category_list = Category.objects.order_by('-likes')
        
        return render(request, 'rango/categories.html', {'categories': category_list})
    
    
class SearchAddPageView(View):
    @method_decorator(login_required)
    def get(self, request):
        category_id = request.GET['category_id']
        title = request.GET['title']
        url = request.GET['url']
	        
        try:
            category = Category.objects.get(id=int(category_id))
        except Category.DoesNotExist:
            return HttpResponse('Error - category not found.')
        except ValueError:
            return HttpResponse('Error - bad category ID.')
	        
        p = Page.objects.get_or_create(category=category, title=title, url=url)
	        
        pages = Page.objects.filter(category=category).order_by('-views')
        return render(request, 'rango/page_listing.html', {'pages': pages})    

