"""mathplatform URL Configuration

The `urlpatterns` list routes URLs to  For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import viewsquiz_start_page
    2. Add a URL to urlpatterns:  path('', home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from django.views.decorators.cache import cache_page

from accounts.views import StudentMainPageView, StudentCourseListView, StudentCourseDetailView
from courses.views import ManageCourseListView, CourseCreateView, CourseDeleteView, CourseUpdateView, \
    CourseModuleUpdateView, ContentCreateUpdateView, ContentDeleteView, ModuleContentListView, SubjectListView, \
    CourseListView, CourseDetailView, enroll_to_course, un_enroll_from_course, ModuleOrderView, ContentOrderView
from main import settings
from question_bank.views import ManageQuestionBankListView, QuestionBankDeleteView, \
    QuestionBankListView, QuestionBankDetailView, QuestionBankCreateView, \
    QuestionBankUpdateView, QuestionBankContentCreateUpdateView, QuestionBankManagerView, QuestionBankContentDeleteView, \
    generate_question, QuestionBankGeneratorFormView
from quiz.views import QuizManageListView, QuizCreateUpdateView, QuizContentDeleteView, StudentQuizStartView, QuizTake, \
    QuizUserProgressView, QuizMarkingList, QuizMarkingDetail, QuizResults

urlpatterns = [
    path('jet/', include('jet.urls', 'jet')),
    path('jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('accounts/', include('allauth.urls')),

    path('', StudentMainPageView.as_view(), name='student_main_page'),

    path('courses/', include([
        path('mine/', ManageCourseListView.as_view(), name='manage_course_list'),
        path('create/', CourseCreateView.as_view(), name='course_create'),
        path('<pk>/delete/', CourseDeleteView.as_view(), name='course_delete'),
        path('<pk>/edit/', CourseUpdateView.as_view(), name='course_edit'),

        path('<pk>/module/', CourseModuleUpdateView.as_view(), name='course_module_update'),
        path('module/<int:module_id>/content/<model_name>/create/', ContentCreateUpdateView.as_view(),
             name='module_content_create'),
        path('module/<int:module_id>/content/<model_name>/<id>/', ContentCreateUpdateView.as_view(),
             name='module_content_update'),
        path('content/<int:id>/delete/', ContentDeleteView.as_view(), name='module_content_delete'),
        path('module/<int:module_id>/', ModuleContentListView.as_view(), name='module_content_list'),

        path('subject/', SubjectListView.as_view(), name='subject_list'),
        path('subject/<slug:subject>/', CourseListView.as_view(), name='course_list_subject'),
        path('<slug:slug>/', CourseDetailView.as_view(), name='course_detail'),

        path('ajax/', include([

            path('module/order/', ModuleOrderView.as_view(), name='module_order'),
            path('content/order/', ContentOrderView.as_view(), name='content_order'),
            path('enroll/to/course/', enroll_to_course, name='enroll_to_course'),
            path('un/enroll/from/course/', un_enroll_from_course, name='un_enroll_from_course'),
        ])),
    ])),

    path('quiz/', include([
        path('manager/', include([
            path('progress/', QuizUserProgressView.as_view(), name='quiz_progress'),
            path('marking/', QuizMarkingList.as_view(), name='quiz_marking'),
            path('marking/<int:pk>/', QuizMarkingDetail.as_view(), name='quiz_marking_detail'),
            path('<slug:slug>/', QuizManageListView.as_view(), name='question_list_manager'),
            path('<slug:slug>/content/<model_name>/create/', QuizCreateUpdateView.as_view(),
                 name='quiz_content_create'),
            path('<slug:slug>/content/<model_name>/<int:id>/update/', QuizCreateUpdateView.as_view(),
                 name='quiz_content_update'),
            path('<int:pk>/delete/', QuizContentDeleteView.as_view(), name='quiz_content_delete'),
        ])),
    ])),

    path('question-bank/', include([
        path('', QuestionBankListView.as_view(), name='question_bank_list'),
        path('<int:pk>/', QuestionBankDetailView.as_view(), name='question_bank_detail'),

        path('manage/', include([
            path('mine/', ManageQuestionBankListView.as_view(), name='question_bank_mine'),
            path('create/', QuestionBankCreateView.as_view(), name='question_bank_create'),
            path('<int:pk>/update/', QuestionBankUpdateView.as_view(), name='question_bank_update'),
            path('<int:pk>/delete/', QuestionBankDeleteView.as_view(), name='question_bank_delete'),

            path('<int:pk>/manager/', QuestionBankManagerView.as_view(), name='question_bank_manager'),
            path('<int:pk>/content/', include([
                path('generate/question/bank/', QuestionBankGeneratorFormView.as_view(), name='generate_question_bank'),
                path('generate/question/', generate_question, name='generate_question'),
                path('<model_name>/create/', QuestionBankContentCreateUpdateView.as_view(),
                     name='question_bank_content_create'),
                path('<model_name>/<int:content_id>/update/', QuestionBankContentCreateUpdateView.as_view(),
                     name='question_bank_content_update'),
                path('<int:content_id>/delete/', QuestionBankContentDeleteView.as_view(),
                     name='question_bank_content_delete'),
            ]))
        ])),

    ])),

    path('account/', include([
        path('main/', StudentMainPageView.as_view(), name='student_main_page'),
        path('courses/', StudentCourseListView.as_view(), name='student_course_list'),
        path('course/<pk>/', cache_page(60 * 15)(StudentCourseDetailView.as_view()), name='student_course_detail'),
        path('course/<pk>/<module_id>/', cache_page(60 * 15)(StudentCourseDetailView.as_view()),
             name='student_course_detail_module'),
        path('quiz/<slug:slug>/', StudentQuizStartView.as_view(), name='quiz_start'),
        path('quiz/<slug:slug>/take/<int:question_index>/', QuizTake.as_view(), name='quiz_start'),
        path('quiz/<slug:slug>/results/', QuizResults.as_view(), name='quiz_results'),
    ])),

    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
