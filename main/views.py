from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .models import AdvUser,SubRubric,Bb,Comment
from .form import ChangeUserInfoForm, RegisterUserForm
from django.contrib.auth.views import PasswordChangeView
from django.views.generic.base import TemplateView
from django.core.signing import BadSignature
from .utilities import signer
from django.views.generic.edit import DeleteView
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .form import SeachForm,Bbform,AIFormSet,UserCommentForm,GuestCoomentForm
from django.shortcuts import redirect


# Create your views here.


def index(request):
    bbs=Bb.objects.filter(is_active=True)[:10]
    context={'bbs':bbs}
    return render(request, 'main/index.html',context)


def other_page(request, page):
    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request=request))


class BbloginView(LoginView):
    template_name = 'main/login.html'


@login_required
def profile(request):
    bbs=Bb.objects.filter(author=request.user.pk)
    context={'bbs':bbs}
    return render(request, 'main/profile.html',context)


class BbLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'main/logout.html'


class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = AdvUser
    template_name = 'main/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Данные изменены'

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


class BBPasswordChangeView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    template_name = 'main/password_change.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль пользователя изменен'


class RegistrerUserView(CreateView):
    model = AdvUser
    template_name = 'main/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main:register_done')


class RegisterDoneView(TemplateView):
    template_name = 'main/register_done.html'


def user_activate(request, sing):
    try:
        username = signer.unsign(sing)
    except BadSignature:
        return render(request, 'main:bad_signature.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template = 'main/user_is_activated.html'
    else:
        template = 'main/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)


class DeleteUserView(LoginRequiredMixin, DeleteView):
    model = AdvUser
    template_name = 'main/delete_user.html'
    success_url = reverse_lazy('main:index')

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super(DeleteUserView, self).setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.add_message(request, messages.SUCCESS, 'SHIP ON FUCK')
        return super(DeleteUserView, self).post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

def by_rubric(request,pk):
    rubric=get_object_or_404(SubRubric,pk=pk)
    bbs=Bb.objects.filter(is_active=True,rubric=pk)
    if 'keyword' in request.GET:
        keyword=request.GET['keyword']
        q=Q(title__icontains=keyword)|Q(content__icontains=keyword)
        bbs=bbs.filter(q)
    else:
        keyword=''
    form=SeachForm(initial={'keyword':keyword})
    paginator=Paginator(bbs,2)
    if 'page' in request.GET:
        page_num=request.GET['page']
    else:
        page_num=1
    page=paginator.get_page(page_num)
    context={'rubric':rubric, 'page':page,'bbs':page.object_list,
             'form':form}
    return render(request,'main/by_rubric.html',context)

def detail(request,rubric_pk,pk):
    bb=Bb.objects.get(pk=pk)
    ais=bb.additionalimage_set.all()
    comments=Comment.objects.filter(bb=pk,is_active=True)
    initial={'bb':bb.pk}
    if request.user.is_authenticated:
        initial['author']=request.user.username
        form_class=UserCommentForm
    else:
        form_class=GuestCoomentForm
    form=form_class(initial=initial)
    if request.method=='POST':
        c_form=form_class(request.POST)
        if c_form.is_valid():
            c_form.save()
            messages.add_message(request,messages.SUCCESS,'Коммент добавлен')
        else:
            form=c_form
            messages.add_message(request,messages.WARNING,'Комментарий не добавлен')
    context={'bb':bb,'ais':ais,'comments':comments,'form':form}
    return render(request,'main/detail.html',context)



    context={'bb':bb,'ais':ais}
    return render(request,'main/detail.html',context)

@login_required
def profile_bb_detail(request,rubric_pk,pk):
    bb = get_object_or_404(Bb, pk=pk)
    ais = bb.additionalimage_set.all()
    context = {'bb': bb, 'ais': ais}
    return render(request, 'main/profile_bb_detail.html', context)

@login_required
def profile_bb_add(request):
    if request.method=='POST':
        form=Bbform(request.POST,request.FILES)
        if form.is_valid():
            bb=form.save()
            formset=AIFormSet(request.POST,request.FILES,instance=bb)
            if formset.is_valid():
                formset.save()
                messages.add_message(request,messages.SUCCESS,'Объявление добавлено')
                return redirect('main:profile')

    else:
        form=Bbform(initial={'author':request.user.pk})
        formset=AIFormSet()
    context={'form':form,'formset':formset}
    return render(request,'main/profile_bb_add.html',context)

@login_required
def profile_bb_change(request,pk):
    bb=get_object_or_404(Bb,pk=pk)
    if request.method=='POST':
        form=Bbform(request.POST,request.FILES,instance=bb)
        if form.is_valid():
            bb=form.save()
            formset=AIFormSet(request.POST,request.FILES,instance=bb)
            if formset.is_valid():
                formset.save()
                messages.add_message(request,messages.SUCCESS,'Объявление исправленно')
                return redirect('main:profile')
    else:
        form=Bbform(instance=bb)
        formset=AIFormSet(instance=bb)
    context={'form':form,'formset':formset}
    return render(request,'main/profile_bb_change.html',context)

@login_required
def profile_bb_delete(request,pk):
    bb=get_object_or_404(Bb,pk=pk)
    if request.method=='POST':
        bb.delete()
        messages.add_message(request,messages.SUCCESS,'Объявление удалено')
        return redirect('main:profile')
    else:
        context={'bb':bb}
        return render(request,'main/profile_bb_delete.html',context)



