# registration/serializers.py
from rest_framework import serializers
from .models import Registration, Paper, AccompanyingPerson

class PaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paper
        fields = ['paper_number', 'title', 'is_additional']

class AccompanyingPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccompanyingPerson
        fields = ['name', 'gala_dinner', 'social_program', 'menu_type']

class RegistrationSerializer(serializers.ModelSerializer):
    papers = PaperSerializer(many=True, read_only=True)
    accompanying_person = AccompanyingPersonSerializer(read_only=True)
    
    class Meta:
        model = Registration
        fields = '__all__'
        read_only_fields = ['registration_id', 'fee_code', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Handle nested creation
        papers_data = self.context.get('papers', [])
        accompanying_data = self.context.get('accompanying_person', None)
        
        registration = Registration.objects.create(**validated_data)
        
        # Create papers
        for paper_data in papers_data:
            Paper.objects.create(registration=registration, **paper_data)
        
        # Create accompanying person
        if accompanying_data:
            AccompanyingPerson.objects.create(registration=registration, **accompanying_data)
        
        return registration