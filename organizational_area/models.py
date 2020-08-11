import os

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext as _

from . settings import *

STRUCTURES_FOLDER = getattr(settings, 'STRUCTURES_FOLDER', STRUCTURES_FOLDER)
LOGOS_FOLDER = getattr(settings, 'LOGOS_FOLDER', LOGOS_FOLDER)


def _logo_upload(instance, filename):
    """
    Returns the location to upload the logo file
    """
    folder = instance.get_logo_folder()
    return os.path.join('{}/{}'.format(folder, filename))


class OrganizationalStructureType(models.Model):
    """
    Classroom, department, secretary, center, service (canteen, accommodation ...)
    """
    name = models.CharField(max_length=128, blank=True, unique=True)
    description = models.TextField(max_length=768, null=True,blank=True)
    create_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Organizational Structure type")
        verbose_name_plural = _("Organizational Structure types")

    def __str__(self):
        return '{}'.format(self.name)


class OrganizationalStructure(models.Model):
    """
    Department, structure
    """
    name = models.CharField(max_length=255, blank=True, unique=True)
    slug = models.SlugField(max_length=255,
                            blank=False, null=False, unique=True,
                            validators=[
                                RegexValidator(
                                    regex='^(?=.*[a-zA-Z])',
                                    message=_("Lo slug deve contenere "
                                              "almeno un carattere alfabetico"),
                                    code='invalid_slug'
                                ),
                            ])
    unique_code = models.CharField(max_length=255, blank=True, unique=True)
    structure_type = models.ForeignKey(OrganizationalStructureType,
                                       null=True, blank=True,
                                       on_delete=models.SET_NULL)
    description = models.TextField(max_length=1024, null=True,blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    banner = models.ImageField(upload_to=_logo_upload,
                               null=True, blank=True,
                               max_length=255)
    url = models.CharField(max_length=768, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Organizational Structure")
        verbose_name_plural = _("Organizational Structures")

    # OnCreate -> signals.py per creazione ufficio di Default
    def get_default_office(self):
        """
        Returns the default structure office
        """
        office = OrganizationalStructureOffice.objects.filter(organizational_structure=self,
                                                              is_default=True).first()
        if office: return office

    def get_folder(self):
        """
        Returns structure attachments folder path
        """
        folder = '{}/{}'.format(STRUCTURES_FOLDER, self.slug)
        return folder

    def get_logo_folder(self):
        """
        Returns logos folder path
        """
        folder = '{}/{}'.format(LOGOS_FOLDER, self.slug)
        return folder

    def __str__(self):
        if not self.structure_type:
            return self.name
        return '{}, {}'.format(self.name, self.structure_type)


class OrganizationalStructureFunction(models.Model):
    """
    Organizational structure function
    """
    name = models.CharField(max_length=128, blank=True, unique=True)
    description = models.TextField(max_length=768, null=True,blank=True)
    create_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Organizational Structure function")
        verbose_name_plural = _("Organizational Structure functions")

    def __str__(self):
        return '{}'.format(self.name)


class EquipmentType(models.Model):
    """
    Equipment
    """
    name = models.CharField(max_length=128, blank=True, unique=True)
    description = models.TextField(max_length=1024, null=True,blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Equipment Type")
        verbose_name_plural = _("Equipments Type")

    def __str__(self):
        return '{}'.format(self.name)


class AbstractLocation(models.Model):
    """
    Location
    """
    address = models.CharField(max_length=768, null=True,blank=True)
    coordinate = models.CharField(max_length=64, null=True,blank=True)
    srs = models.CharField(max_length=13, null=True,blank=True,
                           help_text=_("riferimento spaziale coordinate"))
    description_short = models.CharField(max_length=255, null=True,blank=True)
    funcionality = models.ManyToManyField(OrganizationalStructureFunction,
                                          blank=True)
    equipment = models.ManyToManyField(EquipmentType)
    phone =  models.CharField(max_length=135, null=True,blank=True)
    description_short = models.CharField(max_length=255, null=True,
                                         blank=True)
    description = models.TextField(max_length=1024, null=True,blank=True)
    note = models.TextField(max_length=1024, null=True, blank=True,
                            help_text=_("Descrivere lo stato della struttura nella location."
                                        " Esempio: Momentaneamente chiusa, allagata, problemi"
                                        " lavori in corso, previsioni"))
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class OrganizationalStructureLocation(AbstractLocation):
    """
    An organizational structure can be located in multiple locations
    """
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.CASCADE)

    class Meta:
        ordering = ['organizational_structure']
        verbose_name = _("Organizational Structure location")
        verbose_name_plural = _("Organizational Structure locations")

    def __str__(self):
        return '{} - {}'.format(self.organizational_structure, self.location)


class OrganizationalStructureOffice(models.Model):
    """
    Organizational structure office
    """
    name = models.CharField(max_length=128, null=False, blank=False)
    slug = models.SlugField(max_length=255,
                            blank=False, null=False)
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=True,blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('slug', 'organizational_structure')
        ordering = ['name']
        verbose_name = _("Organizational Structure Office")
        verbose_name_plural = _("Organizational Structure Offices")

    def __str__(self):
        return '({}) {}'.format(self.organizational_structure,
                                self.name)


class OrganizationalStructureOfficeLocation(AbstractLocation):
    """
    An organizational structure office can be located in multiple locations
    """
    office = models.ForeignKey(OrganizationalStructureOffice,
                               on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-create_date']
        verbose_name = _("Organizational Structure office location")
        verbose_name_plural = _("Organizational Structure office locations")

    def __str__(self):
        return '{} - {}'.format(self.office, self.address)


class OrganizationalStructureOfficeEmployee(models.Model):
    """
    Employee-office relationship
    """
    employee = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 on_delete=models.CASCADE)
    office = models.ForeignKey(OrganizationalStructureOffice,
                               on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(max_length=1024, null=True,blank=True)

    class Meta:
        unique_together = ("employee", "office")
        ordering = ['-create_date']
        verbose_name = _("Organizational Structure Office Employee")
        verbose_name_plural = _("Organizational Structure Office Employees")

    @classmethod
    def get_default_operator_or_manager(cls, office):
        """
        Returns an use randomly.
        Try to get an office employee if exists.
        Else returns one of managers.
        """
        office_employees = cls.objects.filter(office=office,
                                              employee__is_active=True).order_by('?')
        if not office_employees:
            office_employees = cls.objects.filter(office__name=settings.DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE,
                                                  office__organizational_structure=office.organizational_structure,
                                                  employee__is_active=True).order_by('?')
        random_office_operator = office_employees.first()
        return random_office_operator.employee

    def __str__(self):
        return '{} - {}'.format(self.employee, self.office)


class UserManageOrganizationalStructure(models.Model):
    """
    Organizational structure manager users
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "organizational_structure")
        ordering = ["user"]
