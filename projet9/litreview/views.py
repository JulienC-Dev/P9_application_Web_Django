from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.list import ListView
from .models import Review, Ticket
from authentication.models import User
from litreview.forms import Create_ticket, Modified_ticket, Create_critique
from django.views.generic import CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


class Flux(LoginRequiredMixin, ListView):
    template_name = 'litreview/flux.html'
    model = Review
    context_object_name = 'reviews'

    def get_queryset(self):
        user_following_by = self.request.user.following_by.values('user')
        qs_following = Review.objects.filter(user__in=user_following_by)
        user_review = Review.objects.filter(user=self.request.user)
        qs = user_review.union(qs_following).order_by('-time_created')
        return qs


class CreateTicket(LoginRequiredMixin, CreateView):
    template_name = 'litreview/createticket.html'
    form_class = Create_ticket
    success_url = reverse_lazy('litreview-flux')
    success_message = "Your profile was created successfully"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CritiqueAnswerCreateview(LoginRequiredMixin, CreateView):
    template_name = "litreview/critiqueanswercreate.html"
    success_url = reverse_lazy('litreview-flux')
    form_class = Create_critique

    def get_context_data(self, **kwargs):
        object = super(CritiqueAnswerCreateview, self).get_context_data(**kwargs)
        object['ticket'] = self.get_object()
        return object

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        return Ticket.objects.get(pk=pk)

    def form_valid(self, form):
        ticket_obj = self.get_object()
        form.instance.ticket = ticket_obj
        form.instance.user = self.request.user
        Review.objects.filter(ticket=ticket_obj).update(answer_review=True)
        form.instance.answer_review = True
        return super().form_valid(form)


class CritiqueAnswerModified(LoginRequiredMixin, UpdateView):
    template_name = 'litreview/critiqueanswermodified.html'
    form_class = Create_critique
    model = Review
    success_url = reverse_lazy('litreview-posts')

    def get_context_data(self, **kwargs):
        context = super(CritiqueAnswerModified, self).get_context_data(**kwargs)
        context['ticket'] = self.object.ticket
        return context

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        return Review.objects.get(pk=pk)


class PostUserListView(LoginRequiredMixin, ListView):
    template_name = 'litreview/postuser.html'
    model = Review
    context_object_name = 'reviews'
    success_url = reverse_lazy('litreview-posts')

    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        return Review.objects.filter(user=user)

    def post(self, request):
        try:
            ticket_obj = self.request.POST.get('delete-ticket')
            review_obj = self.request.POST.get('delete-review')
            if ticket_obj is not None:
                Ticket.objects.get(id=ticket_obj).delete()
            if review_obj is not None:
                Review.objects.get(id=review_obj).delete()
        except:
            return redirect(self.success_url)
        return redirect(self.success_url)


class TicketModifiedUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'litreview/modifiedticket.html'
    form_class = Modified_ticket
    model = Ticket
    success_url = reverse_lazy('litreview-flux')


class Abonnement(LoginRequiredMixin, View):
    template_name = 'litreview/abonnement.html'

    def get(self, request):
        dict_query = self.request.GET
        query = dict_query.get('q')
        user_object = None

        if query is not None:
            try:
                user_object = User.objects.get(username=query)
            except:
                message = 'l utilisateur n existe pas'
                return render(request, self.template_name, {'message': message,
                       'userfollows': self.request.user.following_by.all(),
                       'userflollowings': self.request.user.following.all()})

        context = {'object': user_object,
                   'userfollows': self.request.user.following_by.all(),
                   'userflollowings': self.request.user.following.all()}
        return render(request, self.template_name, context)

    def post(self, request):
        dict_query = self.request.POST
        query = dict_query.get('follow')
        if query is not None:
            user = User.objects.get(username=query)
            try:
                target_user = user.following.get(user=user)
                if target_user is not None:
                    context = {'userfollows': self.request.user.following_by.all(),
                               'userflollowings': self.request.user.following.all(),
                               'message': 'Vous êtes déjà abonné'
                               }
                    return render(request, self.template_name, context)
            except:
                user.following.create(followed_user=self.request.user)
                context = {'userfollows': self.request.user.following_by.all(),
                           'userflollowings': self.request.user.following.all()}
                return render(request, self.template_name, context)

        else:
            query = dict_query.get('unfollow')
            user = User.objects.get(username=query)
            self.request.user.following_by.filter(user=user).delete()
            context = {'userfollows': self.request.user.following_by.all(),
                       'userflollowings': self.request.user.following.all()}
            return render(request, self.template_name, context)


@login_required()
def ticket_create(request):
    if request.method == 'POST':
        ticket_form = Create_ticket(request.POST)
        critique_form = Create_critique(request.POST)
        if ticket_form.is_valid() and critique_form.is_valid():
            ticket_form.instance.user = request.user
            ticket = ticket_form.save()
            critique_form.instance.ticket = ticket
            critique_form.instance.user = request.user
            critique_form.save()
            return redirect('litreview-flux')
    else:
        ticket_form = Create_ticket()
        critique_form = Create_critique()
    return render(request, 'litreview/createcritique.html', {'ticket_form': ticket_form, 'critique_form': critique_form})
