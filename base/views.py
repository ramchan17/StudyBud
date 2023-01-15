from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from django.contrib.auth import authenticate,login,logout

from django.db.models import Q
from .models import Room, Topic, Message, User
from .forms import Roomform, UserForm, MyUserCreationForm

# Create your views here.
def loginPage(request):
    page ='login'
    if request.user.is_authenticated:
        return redirect('home')
    if request.method =="POST":
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request,'User does not exists')
        
        user = authenticate(request,email=email, password=password)

        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,'Username or password does not exist')


    context={'page':page}
    return render(request,'base/login_register.html',context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
   
    form = MyUserCreationForm()
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,'An error occured during registration')
    return render(request,'base/login_register.html',{'form':form})


def home(request):
    q =request.GET.get('q') if request.GET.get('q') != None else ''

    rooms =Room.objects.filter(Q(topic__topic__icontains=q) | Q(name__icontains=q)  ).order_by("-updated","-created") # here we imported room class and its objects and getting them all
    room_count = rooms.count()
    topics =Topic.objects.filter()[0:5]


    room_messages = Message.objects.filter(Q(room__topic__topic__icontains=q)).order_by('-created')

    context ={'rooms': rooms,'topics':topics,'room_count':room_count,'room_messages':room_messages}

    return render(request,"base/home.html",context) 


def room(request,pk):
    room = Room.objects.get(id=pk)
    
    room_messages = room.message_set.all().order_by('-created')

    participants = room.participants.all()

    if request.method =='POST':
        print(room)
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room',pk=room.id)

    context ={'room':room,'room_messages':room_messages,'participants':participants}
    return render(request,"base/room.html",context)

def userProfile(request,pk):
    user = User.objects.get(id = pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()


    context={'user': user,'rooms':rooms,'room_messages':room_messages,'topics':topics}
    return render(request,'base/profile.html',context)


@login_required(login_url='login')
def createRoom(request):
    form = Roomform()
    topics = Topic.objects.all()
    
    if request.method =='POST':
        
        form = Roomform(request.POST)
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(topic=topic_name)
        
        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description')
        )
        return redirect('home')
    context ={'form': form,'topics':topics}
    return render(request,'base/room_form.html',context)

@login_required(login_url='login')
def updateRoom(request,pk):

    room = Room.objects.get(id=pk)

    form = Roomform(instance=room)

    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('Only host can update the room')

    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(topic=topic_name)

        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
            
        return redirect('home')

    context ={'form': form,'topics':topics, 'room': room}

    return render(request,"base/room_form.html",context)


@login_required(login_url='login')
def deleteRoom(request,pk):

    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('Only the owner can delete')

    if request.method =='POST':
        room.delete()
        return redirect('home')

    return render(request,'base/delete.html',{'object':room})

@login_required(login_url='login')
def deleteMessage(request,pk):

    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('Only the owner can delete')

    if request.method =='POST':
        message.delete()
        return redirect('room', pk)

    return render(request,'base/delete.html',{'object':message})


@login_required(login_url='login')
def updateUser(request,pk):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST,request.FILES,  instance=user)
        
        if form.is_valid():
            form.save()
            return redirect('profile',pk=user.id)

    return render(request,'base/update-user.html',{'form':form})


def topicsPage(request):
    q =request.GET.get('q') if request.GET.get('q') != None else ''
    topics =Topic.objects.filter(Q(topic__icontains=q))
    


    return render(request,'base/topics.html',{'topics':topics})

def activityPage(request):
    room_messages = Message.objects.all().order_by('-created')


    return render(request,'base/activity.html',{'room_messages':room_messages})