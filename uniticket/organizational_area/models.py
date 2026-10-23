import os

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from . settings import (DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE,
                        LOGOS_FOLDER,
                        STRUCTURES_FOLDER)


def _logo_upload(instance, filename):
    """Return the upload path of a structure banner.

    Args:
        instance: The OrganizationalStructure that owns the banner.
        filename: The name of the uploaded file.

    Returns:
        The path of the file, relative to MEDIA_ROOT.
    """
    folder = instance.get_logo_folder()
    return os.path.join('{}/{}'.format(folder, filename))


class OrganizationalStructureType(models.Model):
    """Type of a structure: department, secretariat, center, service..."""
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
    """Top level organizational unit (e.g. a department).

    Ticket categories, offices and managers belong to a structure.
    On creation a default office is added by signals.create_manager_office.
    """
    name = models.CharField(max_length=255, blank=True, unique=True)
    # Used in URLs: the validator rejects numeric-only slugs.
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
    # Enables the App IO services configuration for the structure.
    app_io_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Organizational Structure")
        verbose_name_plural = _("Organizational Structures")

    def get_employees(self, **kwargs):
        """Return the employee-office relationships of all structure offices.

        A user employed in more offices appears once per office.

        Args:
            **kwargs: Extra filters on OrganizationalStructureOfficeEmployee.

        Returns:
            QuerySet of OrganizationalStructureOfficeEmployee.
        """
        offices_pks = self.get_offices().values_list('pk', flat=True)
        return OrganizationalStructureOfficeEmployee.objects.filter(
            office__pk__in=offices_pks, **kwargs
        )

    def get_offices(self, **kwargs):
        """Return the structure offices.

        Args:
            **kwargs: Extra filters on OrganizationalStructureOffice.

        Returns:
            QuerySet of OrganizationalStructureOffice.
        """
        return OrganizationalStructureOffice.objects.filter(
            organizational_structure=self, **kwargs
        )

    def get_default_office(self):
        """Return the structure default office.

        Returns:
            The OrganizationalStructureOffice with is_default=True,
            or None if missing.
        """
        office = OrganizationalStructureOffice.objects.filter(
            organizational_structure=self,
            is_default=True).first()
        if office: return office

    def get_folder(self):
        """Return the folder of the structure attachments.

        Returns:
            The folder path, relative to MEDIA_ROOT.
        """
        folder = '{}/{}'.format(STRUCTURES_FOLDER, self.slug)
        return folder

    def get_logo_folder(self):
        """Return the folder of the structure banner.

        Returns:
            The folder path, relative to MEDIA_ROOT.
        """
        folder = '{}/{}'.format(LOGOS_FOLDER, self.slug)
        return folder

    def get_structure_managers(self):
        """Return the manager assignments of the structure.

        Only users that are also employees of the default office are
        included, as in uni_ticket.utils.user_is_manager.

        Returns:
            QuerySet of UserManageOrganizationalStructure.
        """
        osoe = OrganizationalStructureOfficeEmployee
        default_office_users = osoe.objects.filter(office__organizational_structure=self,
                                                   office__is_default=True).values_list('employee', flat=True)
        umos = UserManageOrganizationalStructure
        manager_users = umos.objects.filter(organizational_structure=self,
                                            user__in=default_office_users)
        return manager_users

    def __str__(self):
        if not self.structure_type:
            return self.name
        return '{}, {}'.format(self.name, self.structure_type)


class OrganizationalStructureFunction(models.Model):
    """Function a location can provide."""
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
    """Type of equipment available in a location."""
    name = models.CharField(max_length=128, blank=True, unique=True)
    description = models.TextField(max_length=1024, null=True,blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Equipment Type")
        verbose_name_plural = _("Equipments Type")

    def __str__(self):
        return '{}'.format(self.name)


class AbstractLocation(models.Model):
    """Common fields of a physical location.

    Address, coordinates, contacts, provided functions and equipment.
    """
    address = models.CharField(max_length=768, null=True,blank=True)
    coordinate = models.CharField(max_length=64, null=True,blank=True)
    # Spatial reference system of the coordinate.
    srs = models.CharField(max_length=13, null=True,blank=True,
                           help_text=_("riferimento spaziale coordinate"))
    description_short = models.CharField(max_length=255, null=True,blank=True)
    funcionality = models.ManyToManyField(OrganizationalStructureFunction,
                                          blank=True)
    equipment = models.ManyToManyField(EquipmentType)
    phone = models.CharField(max_length=135, null=True,blank=True)
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
    """Location of a structure (a structure can have many)."""
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.CASCADE)

    class Meta:
        ordering = ['organizational_structure']
        verbose_name = _("Organizational Structure location")
        verbose_name_plural = _("Organizational Structure locations")


class OrganizationalStructureOffice(models.Model):
    """Office of a structure.

    Tickets and tasks are assigned to offices and handled by their employees.
    """
    name = models.CharField(max_length=128, null=False, blank=False)
    # Unique only inside the structure.
    slug = models.SlugField(max_length=255,
                            blank=False, null=False)
    organizational_structure = models.ForeignKey(
        OrganizationalStructure,
        on_delete=models.CASCADE
    )
    description = models.TextField(max_length=1024, null=True,blank=True)
    # Office created with the structure: its employees can be managers.
    is_default = models.BooleanField(default=False)
    # Hidden to other structures when they transfer a ticket competence.
    is_private = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('slug', 'organizational_structure')
        ordering = ['name']
        indexes = [models.Index(fields=["is_active", "organizational_structure_id"])]
        verbose_name = _("Organizational Structure Office")
        verbose_name_plural = _("Organizational Structure Offices")

    def __str__(self):
        return '({}) {}'.format(self.organizational_structure,
                                self.name)


class OrganizationalStructureOfficeLocation(AbstractLocation):
    """Location of an office (an office can have many)."""
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
    """Assignment of a user (operator) to an office."""
    employee = models.ForeignKey(get_user_model(),
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

    def __str__(self):
        return '{} - {}'.format(self.employee, self.office)


class UserManageOrganizationalStructure(models.Model):
    """Manager role of a user in a structure.

    The role is effective only if the user is also an employee of the
    structure default office.
    """
    user = models.ForeignKey(get_user_model(),
                             on_delete=models.CASCADE)
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "organizational_structure")
        ordering = ["user"]
