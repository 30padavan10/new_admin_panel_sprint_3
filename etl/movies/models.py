import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    created_at = models.DateTimeField(_('created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    """Жанр"""
    name = models.CharField(_('name'), max_length=255)
    # В данном случае null=True указано, потому что в sqlite это поле уже пустое и при переносе записей будет ошибка
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = _('genre')
        verbose_name_plural = _('genres')

    def __str__(self):
        return self.name


class FilmworkType(models.TextChoices):
    MOVIE = 'movie', _('movie')
    TV_SHOW = 'tv_show', _('tv_show')


class Filmwork(UUIDMixin, TimeStampedMixin):
    """Фильм"""
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)
    creation_date = models.DateField(_('creation_date'), blank=True, null=True)
    file_path = models.FileField(_('file'), blank=True, null=True, upload_to='movies/')
    rating = models.FloatField(_('rating'), blank=True, null=True,
                               validators=[MinValueValidator(0),
                                           MaxValueValidator(100)])
    type = models.CharField(_('type'), choices=FilmworkType.choices)
    genres = models.ManyToManyField(Genre, through='GenreFilmwork')
    persons = models.ManyToManyField('Person', through='PersonFilmwork')

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = _('movie')
        verbose_name_plural = _('movies')

    def __str__(self):
        return self.title


class GenreFilmwork(UUIDMixin):
    """Промежуточная таблица Жанр-Фильм"""
    film_work = models.ForeignKey(Filmwork, verbose_name=_('film_work'), on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, verbose_name=_('genre'), on_delete=models.CASCADE)
    created_at = models.DateTimeField(_('created'), auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"
        verbose_name = _('genre')
        verbose_name_plural = _('genres')
        constraints = [
            models.UniqueConstraint(fields=['film_work', 'genre'], name='film_work_genre_uniq')
        ]
        indexes = [
            models.Index(fields=['film_work', 'genre'], name='film_work_genre_idx'),
        ]

    def __str__(self):
        return self.genre.name


class Person(UUIDMixin, TimeStampedMixin):
    """Личность"""
    full_name = models.CharField(_('full_name'), max_length=255)

    class Meta:
        db_table = "content\".\"person"
        verbose_name = _('person')
        verbose_name_plural = _('persons')

    def __str__(self):
        return self.full_name


class FilmworkPersonRoleType(models.TextChoices):
    DIRECTOR = 'director', _('director')
    WRITER = 'writer', _('writer')
    ACTOR = 'actor', _('actor')


class PersonFilmwork(UUIDMixin):
    """Промежуточная таблица Личность-Фильм"""
    film_work = models.ForeignKey(Filmwork, verbose_name=_('film_work'), on_delete=models.CASCADE)
    person = models.ForeignKey(Person, verbose_name=_('person'), on_delete=models.CASCADE)
    role = models.TextField(_('role'), choices=FilmworkPersonRoleType.choices)
    created_at = models.DateTimeField(_('created'), auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"
        verbose_name = _('person')
        verbose_name_plural = _('persons')
        constraints = [
            models.UniqueConstraint(fields=['film_work', 'person', 'role'], name='film_work_person_role_uniq')
        ]
        indexes = [
            models.Index(fields=['film_work', 'person', 'role'], name='film_work_person_role_idx'),
        ]

    def __str__(self):
        return self.person.full_name
