from rest_framework import viewsets, status, generics, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count, Q

from .models import (
    ProductRating, ReviewImage, ReviewVote, ProductQuestion, 
    ProductAnswer, Product
)
from .extended_serializers import (
    ProductRatingWithVotesSerializer, ReviewImageSerializer, ReviewVoteSerializer,
    ProductQuestionSerializer, ProductAnswerSerializer
)
from notifications.utils import create_notification


class ProductRatingViewSet(viewsets.ModelViewSet):
    """
    Enhanced Product Rating/Review ViewSet with voting support
    
    Endpoints:
    - GET /api/products/ratings/ - List all ratings
    - POST /api/products/ratings/ - Create rating/review
    - GET /api/products/ratings/{id}/ - Get specific rating
    - PUT /api/products/ratings/{id}/ - Update own rating
    - DELETE /api/products/ratings/{id}/ - Delete own rating
    - POST /api/products/ratings/{id}/vote/ - Vote on review (helpful/not helpful)
    - POST /api/products/ratings/{id}/add_image/ - Add image to review
    """
    serializer_class = ProductRatingWithVotesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter ratings by product if specified"""
        queryset = ProductRating.objects.all()
        
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by rating if specified
        rating_filter = self.request.query_params.get('rating')
        if rating_filter:
            queryset = queryset.filter(rating=rating_filter)
        
        # Sort by helpful votes by default
        return queryset.annotate(
            helpful_count=Count('votes', filter=Q(votes__vote_type='helpful'))
        ).order_by('-helpful_count', '-created_at')
    
    def perform_create(self, serializer):
        """Create rating and notify vendor"""
        product_id = self.request.data.get('product')
        product = Product.objects.get(id=product_id)
        
        # Check if user already rated this product
        existing_rating = ProductRating.objects.filter(
            product=product, 
            user=self.request.user
        ).first()
        
        if existing_rating:
            raise serializers.ValidationError(
                "You have already rated this product. Use PUT to update."
            )
        
        rating = serializer.save(user=self.request.user, product=product)
        
        # Notify vendor
        if hasattr(product.vendor.user, 'email'):
            create_notification(
                user=product.vendor.user,
                notification_type='system',
                title='New Product Review',
                message=f'{self.request.user.username} left a {rating.rating}-star review on {product.name}',
                reference_id=str(product.id)
            )
    
    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """
        Vote on a review as helpful or not helpful
        
        Body: {"vote_type": "helpful" or "not_helpful"}
        """
        rating = self.get_object()
        vote_type = request.data.get('vote_type')
        
        if vote_type not in ['helpful', 'not_helpful']:
            return Response(
                {'detail': 'vote_type must be "helpful" or "not_helpful"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already voted
        existing_vote = ReviewVote.objects.filter(
            review=rating,
            user=request.user
        ).first()
        
        if existing_vote:
            # Update existing vote
            existing_vote.vote_type = vote_type
            existing_vote.save()
            message = 'Vote updated'
        else:
            # Create new vote
            ReviewVote.objects.create(
                review=rating,
                user=request.user,
                vote_type=vote_type
            )
            message = 'Vote recorded'
        
        # Return updated counts
        helpful_votes = rating.votes.filter(vote_type='helpful').count()
        not_helpful_votes = rating.votes.filter(vote_type='not_helpful').count()
        
        return Response({
            'detail': message,
            'helpful_votes': helpful_votes,
            'not_helpful_votes': not_helpful_votes,
            'your_vote': vote_type
        })
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def add_image(self, request, pk=None):
        """Add image to review"""
        rating = self.get_object()
        
        # Verify user owns this review
        if rating.user != request.user:
            return Response(
                {'detail': 'You can only add images to your own reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        image = request.FILES.get('image')
        if not image:
            return Response(
                {'detail': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        review_image = ReviewImage.objects.create(review=rating, image=image)
        
        return Response({
            'detail': 'Image added successfully',
            'image': ReviewImageSerializer(review_image).data
        }, status=status.HTTP_201_CREATED)


class ProductQuestionViewSet(viewsets.ModelViewSet):
    """
    Product Q&A ViewSet
    
    Endpoints:
    - GET /api/products/questions/ - List questions (filter by product)
    - POST /api/products/questions/ - Ask a question
    - GET /api/products/questions/{id}/ - Get question with answers
    - DELETE /api/products/questions/{id}/ - Delete own question
    """
    serializer_class = ProductQuestionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter questions by product if specified"""
        queryset = ProductQuestion.objects.all()
        
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Show unanswered questions first
        return queryset.order_by('is_answered', '-created_at')
    
    def perform_create(self, serializer):
        """Create question and notify vendor"""
        product_id = self.request.data.get('product')
        product = Product.objects.get(id=product_id)
        
        question = serializer.save(user=self.request.user, product=product)
        
        # Notify vendor
        if hasattr(product.vendor.user, 'email'):
            create_notification(
                user=product.vendor.user,
                notification_type='system',
                title='New Product Question',
                message=f'{self.request.user.username} asked about {product.name}',
                reference_id=str(question.id)
            )
    
    def perform_destroy(self, instance):
        """Only allow users to delete their own questions"""
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own questions")
        instance.delete()


class ProductAnswerViewSet(viewsets.ModelViewSet):
    """
    Product Answer ViewSet
    
    Endpoints:
    - GET /api/products/answers/ - List answers (filter by question)
    - POST /api/products/answers/ - Answer a question
    - PUT /api/products/answers/{id}/ - Update own answer
    - DELETE /api/products/answers/{id}/ - Delete own answer
    - POST /api/products/answers/{id}/vote_helpful/ - Vote answer as helpful
    """
    serializer_class = ProductAnswerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter answers by question if specified"""
        queryset = ProductAnswer.objects.all()
        
        question_id = self.request.query_params.get('question_id')
        if question_id:
            queryset = queryset.filter(question_id=question_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create answer and notify question asker"""
        question_id = self.request.data.get('question')
        question = ProductQuestion.objects.get(id=question_id)
        
        # Check if answerer is the product vendor
        is_vendor = hasattr(self.request.user, 'vendor_profile') and \
                   question.product.vendor == self.request.user.vendor_profile
        
        answer = serializer.save(
            user=self.request.user,
            question=question,
            is_vendor=is_vendor
        )
        
        # Mark question as answered
        if not question.is_answered:
            question.is_answered = True
            question.save()
        
        # Notify question asker
        create_notification(
            user=question.user,
            notification_type='system',
            title='Your Question Was Answered',
            message=f'{"Vendor" if is_vendor else "Someone"} answered your question about {question.product.name}',
            reference_id=str(answer.id)
        )
    
    @action(detail=True, methods=['post'])
    def vote_helpful(self, request, pk=None):
        """Vote answer as helpful"""
        answer = self.get_object()
        
        # Increment helpful votes
        answer.helpful_votes += 1
        answer.save()
        
        return Response({
            'detail': 'Vote recorded',
            'helpful_votes': answer.helpful_votes
        })


class ProductQAListView(generics.ListAPIView):
    """
    Convenient endpoint to get all Q&A for a product
    
    GET /api/products/{product_id}/qa/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, product_id):
        """Get all questions and answers for a product"""
        questions = ProductQuestion.objects.filter(product_id=product_id)
        
        qa_data = []
        for question in questions:
            answers = ProductAnswer.objects.filter(question=question)
            
            qa_data.append({
                'question': ProductQuestionSerializer(question).data,
                'answers': ProductAnswerSerializer(answers, many=True).data
            })
        
        return Response({
            'product_id': product_id,
            'total_questions': questions.count(),
            'qa': qa_data
        })

