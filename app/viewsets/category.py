from rest_framework import status,viewsets,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from app.models import *
from app.serializers import * 
from app.scripts import extractToken,utils,checkOrganizerPlan,utils

class CategoryViewSet(viewsets.ModelViewSet):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def create(self, request, *args, **kwargs):

        admin = extractToken.checkAdminToken(request.headers)
        return super().create(request, *args, **kwargs)

    @action(detail=True,methods=['POST'])
    def createSubCategory(self,request,pk = None,format = None):

        admin = extractToken.checkAdminToken(request.headers)

        if 'title' not in request.data:
            raise ValueError("All required fields must be input")
        
        checkCategory = Category.objects.filter(pk = pk)
        if not checkCategory.exists():
            raise ValueError("Category with the id does not exist")
        
        createdSubCategory = SubCategory.objects.create(
            title = request.data['title'],
            category = checkCategory[0]    
        )

        return Response({
            "success":True,
            "message":"Successfully created the sub-category",
            "sub-category":{
                "title":createdSubCategory.title,
                "id":createdSubCategory.id,
                "category":createdSubCategory.category.title,
                "category_id":createdSubCategory.category.id
            }
        })
    
    @action(detail = False, methods = ['GET'])
    def categoriesWithEvent(self, request , format = None):
        
        categoryIds = Event.objects.values_list('subCategory__category').distinct()
        
        categoryIdsList = []
        for id in categoryIds:
            categoryIdsList.append(id[0])

        categories = Category.objects.filter(pk__in= categoryIdsList)

        allCategories = []
        for category in categories:
            singleCategory = {}
            singleCategory['id'] = category.id
            singleCategory['title'] = category.title

            allCategories.append(singleCategory)

        return Response({
            "success":True,
            "data":allCategories
        })

    @action(detail=True,methods=['GET'])
    def subCategories(self,request,pk=None,format=None):
        checkCategory = Category.objects.filter(pk = pk)
        if not checkCategory.exists():
            raise ValueError("Category with the id does not exist")
        
        checkSubCategories = SubCategory.objects.filter(category = checkCategory[0])
        allSubCatgories = []

        if not checkSubCategories.exists():
            return Response({
                    "success":False,
                    "sub-categories":[]
                })

        for subCategory in checkSubCategories:
            singleSubCategory = {}

            singleSubCategory['title'] = subCategory.title
            singleSubCategory['id'] = subCategory.id
            singleSubCategory['category'] = subCategory.category.title
            singleSubCategory['category_id'] = subCategory.category.id

            allSubCatgories.append(singleSubCategory)


        return Response({
            "success":True,
            "sub-categories":allSubCatgories
        })

    @action(detail=False,methods=['GET'],url_path='getEventByCategory/(?P<category>[A-z0-9]+)')
    def getEventByCategory(self,request,format=None,*args, **kwargs):

        checkCategory = Category.objects.filter(title = kwargs['category'],isHidden__in = [False])

        if not checkCategory.exists():
            raise ValueError("Category does not exist")
        
        getEventsByCategory = Event.objects.filter(subCategory__category=checkCategory[0])

        return Response({
            "success":True,
            "data": utils.eventFormatter(getEventsByCategory)
        })
