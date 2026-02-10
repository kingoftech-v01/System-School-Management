from django import forms
from django.db import transaction
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
)
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from course.models import Program
from .models import User, Student, Parent, InvitationCode, RELATION_SHIP, LEVEL, GENDERS


class StaffAddForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Username",
        required=False,
    )

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="First Name",
    )

    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Last Name",
    )

    gender = forms.CharField(
        widget=forms.Select(
            choices=GENDERS,
            attrs={
                "class": "browser-default custom-select form-control",
            },
        ),
    )

    address = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Address",
    )

    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Mobile No.",
    )

    email = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Email",
    )

    password1 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label="Password",
        required=False,
    )

    password2 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label="Password Confirmation",
        required=False,
    )

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic()
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_lecturer = True
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.phone = self.cleaned_data.get("phone")
        user.address = self.cleaned_data.get("address")
        user.email = self.cleaned_data.get("email")

        if commit:
            user.save()

        return user


class StudentAddForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={"type": "text", "class": "form-control", "id": "username_id"}
        ),
        label="Username",
        required=False,
    )
    address = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Address",
    )

    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Mobile No.",
    )

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="First name",
    )

    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Last name",
    )

    gender = forms.CharField(
        widget=forms.Select(
            choices=GENDERS,
            attrs={
                "class": "browser-default custom-select form-control",
            },
        ),
    )

    level = forms.CharField(
        widget=forms.Select(
            choices=LEVEL,
            attrs={
                "class": "browser-default custom-select form-control",
            },
        ),
    )

    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        widget=forms.Select(
            attrs={"class": "browser-default custom-select form-control"}
        ),
        label="Program",
    )

    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control",
            }
        ),
        label="Email Address",
    )

    password1 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label="Password",
        required=False,
    )

    password2 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label="Password Confirmation",
        required=False,
    )

    # def validate_email(self):
    #     email = self.cleaned_data['email']
    #     if User.objects.filter(email__iexact=email, is_active=True).exists():
    #         raise forms.ValidationError("Email has taken, try another email address. ")

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic()
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.gender = self.cleaned_data.get("gender")
        user.address = self.cleaned_data.get("address")
        user.phone = self.cleaned_data.get("phone")
        user.address = self.cleaned_data.get("address")
        user.email = self.cleaned_data.get("email")

        if commit:
            user.save()
            Student.objects.create(
                student=user,
                level=self.cleaned_data.get("level"),
                program=self.cleaned_data.get("program"),
            )

        return user


class ProfileUpdateForm(UserChangeForm):
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control",
            }
        ),
        label="Email Address",
    )

    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="First Name",
    )

    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Last Name",
    )

    gender = forms.CharField(
        widget=forms.Select(
            choices=GENDERS,
            attrs={
                "class": "browser-default custom-select form-control",
            },
        ),
    )

    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Phone No.",
    )

    address = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Address / city",
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "gender",
            "email",
            "phone",
            "address",
            "picture",
        ]


class ProgramUpdateForm(UserChangeForm):
    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        widget=forms.Select(
            attrs={"class": "browser-default custom-select form-control"}
        ),
        label="Program",
    )

    class Meta:
        model = Student
        fields = ["program"]


class EmailValidationOnForgotPassword(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            msg = "There is no user registered with the specified E-mail address. "
            self.add_error("email", msg)
            return email


class ParentAddForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Username",
    )
    address = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Address",
    )

    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Mobile No.",
    )

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="First name",
    )

    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label="Last name",
    )

    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control",
            }
        ),
        label="Email Address",
    )

    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.Select(
            attrs={"class": "browser-default custom-select form-control"}
        ),
        label="Student",
    )

    relation_ship = forms.CharField(
        widget=forms.Select(
            choices=RELATION_SHIP,
            attrs={
                "class": "browser-default custom-select form-control",
            },
        ),
    )

    password1 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label="Password",
    )

    password2 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label="Password Confirmation",
    )

    # def validate_email(self):
    #     email = self.cleaned_data['email']
    #     if User.objects.filter(email__iexact=email, is_active=True).exists():
    #         raise forms.ValidationError("Email has taken, try another email address. ")

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic()
    def save(self):
        user = super().save(commit=False)
        user.is_parent = True
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.address = self.cleaned_data.get("address")
        user.phone = self.cleaned_data.get("phone")
        user.email = self.cleaned_data.get("email")
        user.save()
        parent = Parent.objects.create(
            user=user,
            student=self.cleaned_data.get("student"),
            relation_ship=self.cleaned_data.get("relation_ship"),
        )
        parent.save()
        return user


# ########################################################
# Signup Flow Forms
# ########################################################


class StudentActivationForm(forms.Form):
    """Step 1: Student enters registration number + name to start activation."""

    registration_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g., 24-CS-001",
            }
        ),
        label="Registration Number",
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "First Name",
            }
        ),
        label="First Name",
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last Name",
            }
        ),
        label="Last Name",
    )

    def clean(self):
        cleaned_data = super().clean()
        reg_number = cleaned_data.get("registration_number")
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")

        if not all([reg_number, first_name, last_name]):
            return cleaned_data

        try:
            student = Student.objects.select_related("student").get(
                registration_number=reg_number
            )
        except Student.DoesNotExist:
            raise forms.ValidationError(
                "No student found with this registration number. "
                "Please check your details or contact the school administration."
            )

        user = student.student
        if user.first_name.lower() != first_name.lower() or user.last_name.lower() != last_name.lower():
            raise forms.ValidationError(
                "The name you entered does not match our records. "
                "Please enter your name exactly as registered by the school."
            )

        if user.has_usable_password() and not user.must_change_password:
            raise forms.ValidationError(
                "This student account has already been activated. "
                "Please sign in instead."
            )

        self.student = student
        return cleaned_data


class StudentVerifyParentForm(forms.Form):
    """Step 2: Student enters verification code sent to parent's email."""

    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg text-center",
                "placeholder": "000000",
                "maxlength": "6",
                "style": "letter-spacing: 0.5em; font-size: 1.5em;",
            }
        ),
        label="Verification Code",
    )


class StudentSetPasswordForm(forms.Form):
    """Step 3: Student sets email and password to complete activation."""

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "your@email.com",
            }
        ),
        label="Email Address",
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
            }
        ),
        label="Password",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm Password",
            }
        ),
        label="Confirm Password",
    )

    def __init__(self, *args, user_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_pk = user_pk

    def clean_email(self):
        email = self.cleaned_data["email"]
        qs = User.objects.filter(email__iexact=email)
        if self._user_pk:
            qs = qs.exclude(pk=self._user_pk)
        if qs.exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class InvitationCodeForm(forms.Form):
    """Enter and validate an invitation code."""

    code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg text-center",
                "placeholder": "XXXX-XXXX",
                "style": "letter-spacing: 0.3em; font-size: 1.2em;",
            }
        ),
        label="Invitation Code",
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        try:
            invitation = InvitationCode.objects.get(code=code)
        except InvitationCode.DoesNotExist:
            raise forms.ValidationError("Invalid invitation code.")

        if not invitation.is_valid:
            if invitation.used_at:
                raise forms.ValidationError("This invitation code has already been used.")
            raise forms.ValidationError("This invitation code has expired.")

        self.invitation = invitation
        return code


class ParentInvitationSignupForm(forms.Form):
    """Parent fills in details after validating invitation code."""

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"}),
        label="First Name",
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"}),
        label="Last Name",
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "your@email.com"}),
        label="Email Address",
    )
    phone = forms.CharField(
        max_length=60,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
        label="Phone",
    )
    relation_ship = forms.ChoiceField(
        choices=RELATION_SHIP,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Relationship to Student",
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
        label="Password",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm Password"}),
        label="Confirm Password",
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class StaffInvitationSignupForm(forms.Form):
    """Staff fills in details after validating invitation code."""

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"}),
        label="First Name",
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"}),
        label="Last Name",
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "your@email.com"}),
        label="Email Address",
    )
    phone = forms.CharField(
        max_length=60,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
        label="Phone",
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
        label="Password",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm Password"}),
        label="Confirm Password",
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class ForcePasswordResetForm(forms.Form):
    """Form for forced password reset on first login."""

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "New Password"}),
        label="New Password",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm New Password"}),
        label="Confirm New Password",
    )

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
