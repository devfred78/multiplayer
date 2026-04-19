"""
multiplayer, a Python library for managing multiplayer games
Copyright (C) 2025 [devfred78](https://github.com/devfred78)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

"""This module provides tools for managing interface languages."""

import logging
from pathlib import Path
import tomllib
import sys

class Language():
    """
    The set of texts that can be displayed on the interface, in a given language, instantiated from a string or a file in TOML format.
    
    During instantiation, a check is performed to ensure that only elements that exist in the `pattern` are taken into account. If additional elements are present, they are silently ignored. On the other hand, import is possible even if the set of imported elements does not completely cover the `pattern` keys.
    
    Parameters:
        file:
            The file or string from which data will be imported. The file can be a pathlib.Path object, or a string describing the relative or absolute path to the file to be imported. It can also be a string containing text in [TOML format](https://toml.io).
            
            ```pycon
            >>> from language import Language
            >>> from pathlib import Path
            >>>
            >>> # The following commands are equivalent:
            >>>
            >>> language1 = Language('/path/to/file/language.lng')
            >>>
            >>> my_file = Path('/path/to/file/language.lng')
            >>> language2 = Language(my_file)
            >>>
            >>> my_str = '''
                [header]
                programme = "Programme Name"
                version = "0.1"
                language = "fr"
                [default]
                area = "FR"
                [FR]
                WHOAMI = "Qui suis-je ?"
                '''
            >>> language3 = Language(my_str)
            ```
        pattern:
            a dict object whose keys will be used to form the instance from the language file. When `pattern` is not empty, only those elements of the loaded file that correspond to the keys will actually be used. If it is empty (default), all elements of the loaded file will be used.
            
            Examples:
                If
                
                >>> `pattern` = `{"WHOAMI": "Who am I ?", "NAME": "Name"}
                
                and the language file is
                
                >>> my_lang = '''
                    ...
                    [FR]
                    WHOAMI = "Qui suis-je ?"
                    NAME = "Nom"
                    DEFAULT_NAME = "Joueur"
                    ...
                    '''
                
                then, only WHOAMI and NAME will be loaded, and not DEFAULT_NAME.
        logger:
            The parent logger used to track events that append when the instance is running. Mainly for status monitoring or fault investigation purposes. If None (the default), no event is tracked.
    
    Attributes:
        header:
            Dict object containing the `header` section of the language file. **read-only**. It is normally composed of the following indexes:
            
            |  Index      | value                                                                         |
            | ----------- | ----------------------------------------------------------------------------- |
            | `programme` | Sring containing the name of programme on which the translation is applied    |
            | `version`   | String containing the version of the language file,                           |
            |             | following the [Semantic Versioning Specification](https://semver.org/)        |
            | `language`  | 2-character string representing the language supported by the imported file,  |
            |             | following the [ISO 639.1 standard](https://www.iso.org/iso-639-language-code) |
        usable:
            `True` if the language file has been successfully loaded and decoded, and the Language instance is fully available. `False` otherwise. **read-only**
        countries:
            Tuple of all countries covered by the language file, represented by a 2-character string following the [ISO 3166 alpha-2 standard](https://www.iso.org/iso-3166-country-codes.html)
        all_translations:
            Dict object containing supported countries as keys, and for each, a dict object for the translated elements with the following format {"key 1 in pattern" : "translation 1 found in the language file", "key 2 in pattern": "translation 2 found in the langauge file", ...}. **read-only**
        default_country:
            2-character string representing the default country to be used as key in the all_translations attribute to find the default dictionnary of translated elements. **read-only**
        log:
            The logger used to track events that append when the instance is running. Mainly for status monitoring or fault investigation purposes.
        
    Raises:
        FileNotFoundError:
            Raises if `file` seems to be a file (`Path` object or a path indicated in a string) but the file actually does not exist.
        ValueError:
            Raises if `file` cannot be decoded, either as a string or as an existing `Path` object (but whose content is invalid).
        TypeError:
            Raises if `file` is neither a string nor a `Path` object.
    """
    def __init__(self, file:Path|str, pattern:dict = {}, logger:logging.Logger = None):
        # Language instance initialization
        
        if logger is None:
            self.log = logging.getLogger("Language")
            self.log.addHandler(logging.NullHandler())
        else:
            self.log = logger.getChild("Language")

        self.log.debug("--- Language initialization ---")
        
        self._pattern = pattern
        self._header: dict = {}
        self._usable: bool = False
        self._all_translations: dict = {}
        self._default_country: str = ""
        
        if isinstance(file, Path):
            if file.is_file():
                try:
                    self._load_lng_dict(self._load_Path_file(file))
                except tomllib.TOMLDecodeError:
                    raise ValueError
            else:
                self.log.warning(f"File {file.name} is not present. The expected associated language will not be applied.")
                raise FileNotFoundError
        elif isinstance(file, str):
            try:
                my_file = Path(file)
            except:
                try:
                    self._load_lng_dict(self._parse_str_lng(file))
                except tomllib.TOMLDecodeError:
                    raise ValueError
            else:
                if my_file.is_file():
                    try:
                        self._load_lng_dict(self._load_Path_file(file))
                    except tomllib.TOMLDecodeError:
                        raise ValueError
                else:
                    raise FileNotFoundError
        else:
            raise TypeError
    
    @property
    def header(self) -> dict:
        # Dict object containing the `header` section of the language file. **read-only**
        return self._header
    
    @property
    def usable(self) -> bool:
        # `True` if the language file has been successfully loaded and decoded, and the Language instance is fully available. `False` otherwise. **read-only**
        return self._usable
    
    @property
    def all_translations(self) -> dict:
        # Dict object containing supported countries as keys, and for each, a dict object for the translated elements
        return self._all_translations
    
    @property
    def default_country(self) -> str:
        # 2-character string representing the default country to be used as key in the all_translations attribute to find the default dictionnary of translated elements
        return self._default_country
    
    def _load_Path_file(self, file:Path) -> dict:
        """
        Loads the language file into a dict object.
        
        The file must be in TOML format.
        
        Parameters:
            file:
                The file from which data will be imported.
        
        Returns:
            dict: a representation of the language file in a dict object
        """
        with open(file, "rb") as lang_file:
            try:
                data = tomllib.load(lang_file)
            except tomllib.TOMLDecodeError:
                self.log.warning(f"Language File {file.name} does not respect the expected TOML format. It will be not loaded.")
                self._usable = False
                raise
            else:
                self.log.debug(f"Language file {file.name} successfully loaded.")
                self._usable = True
                return data

    def _parse_str_lng(self, str_lng:str) -> dict:
        """
        Parses a TOML-compliant string, which is supposed to be the content of a language file, and loads it into a dict object.
        
        Parameters:
            str_lng:
                The string from which data will be imported.
        
        Returns:
            dict: a representation of the language string in a dict object
        """
        try:
            data = tomllib.loads(str_lng)
        except tomllib.TOMLDecodeError:
            self.log.warning("The provided string does not respect the expected TOML format. It will be not loaded.")
            self._usable = False
            raise
        else:
            self.log.debug("Provided string successfully loaded.")
            self._usable = True
            return data

    def _load_lng_dict(self, data:dict):
        """
        Loads a dict object supposed to be an extraction of a language file in TOML format, into the relevant attributes of the current instance.
        
        During loading, a check is performed with the `pattern` given as parameter for the instanciation (see description of this parameter at the class level).
        
        Parameters:
            data:
                Extraction of the language file
        
        Returns:
            None
        """
        
        # Reading the header
        try:
            self._header = data['header']
        except KeyError:
            self.log.warning("Header not present in the language file. Language file not usable.")
            self._usable = False
            raise tomllib.TOMLDecodeError
        
        # Reading the supported countries
        self.countries = tuple([index for index in data.keys() if index not in ['header', 'default']])
        self.log.debug(f"The language file supports the following country code{"" if len(self.countries) <= 1 else "s"}: {self.countries}")
        
        # Reading the translated elements for each country
        for country in self.countries:
            imported_elements = {}
            if len(self._pattern.keys()) != 0:
                for element in self._pattern.keys():
                    try:
                        imported_elements[element] = data[country][element]
                    except KeyError:
                        self.log.warning(f"'{element}' not found in the language file for the country {country}")
            else:
                imported_elements = data[country].copy()
            self._all_translations[country] = imported_elements.copy()
        
        # Reading the default country or region
        try:
            self._default_country = data['default']['country']
        except KeyError:
            self.log.warning("The language file has no default country")
            self._default_country = self.countries[0]
            self.log.warning(f"{self._default_country} is used as default country for the language {self.header['language']}")
        else:
            self.log.debug(f"{self._default_country} is the default country for the language {self.header['language']}")

class Languages():
    """
    All languages supported for the interface, with all associated texts.
    
    During instantiation, all compatible language files in the specified directory are automatically recognized and loaded. It is also possible to add and remove a `Language` object that has been initialized before.
    
    To retrieve a `dict` object containing all translated texts, use the form `Languages[key]`, where `key` is a character string of the following form:
    
    `<lang>_<country>`
    
    with `<lang>` a 2-character string specifying the language, according to the [ISO 639.1 standard](https://www.iso.org/iso-639-language-code), and `<country>` a 2-character string specifying the geographical area, according to the [ISO 3166 alpha-2 standard](https://www.iso.org/iso-3166-country-codes.html).
    The underscore character `_` can be replaced by any other character; it carries no meaning other than that of separator.
    
    If `<country>` is not specified, or if it doesn't correspond to any geographical area relative to the specified language, then the `dict` object returned corresponds to the default geographical area of the language in question.
    
    If the first 2 characters of `key` do not correspond to any language supported by the `Languages` instance, then `KeyError` is raised.
    
    Parameters:
        directory:
            The directory where the language files to be loaded are searched. By default, this will be the current directory.
        extension:
            The language file extension, including the dot (.). The default is '.lng'.
        pattern:
            a dict object whose keys will be used to form the instance from the language files. When `pattern` is not empty, only those elements of the loaded file that correspond to the keys will actually be used. If it is empty (default), all elements of the loaded file will be used.
            
            Examples:
                If
                
                >>> `pattern` = `{"WHOAMI": "Who am I ?", "NAME": "Name"}
                
                and the language file is
                
                >>> my_lang = '''
                    ...
                    [FR]
                    WHOAMI = "Qui suis-je ?"
                    NAME = "Nom"
                    DEFAULT_NAME = "Joueur"
                    ...
                    '''
                
                then, only WHOAMI and NAME will be loaded, and not DEFAULT_NAME.
        logger:
            The parent logger used to track events that append when the instance is running. Mainly for status monitoring or fault investigation purposes. If None (the default), no event is tracked.
        
    Attributes:
        supported_languages_iso639:
            Tuple of 2-character strings representing the supported languages, following the [ISO 639.1 standard](https://www.iso.org/iso-639-language-code). **Read-only**.
    
    Raises:
        KeyError:
            Raises when `Languages[key]` is called and `key` does not provide a language supported by the instance.
    """
    if getattr(sys, "frozen", False):
        DEFAULT_DIR = Path(sys.executable).parent
    else:
        DEFAULT_DIR = Path(__file__).resolve().parent
    
    def __init__(self, directory:Path = DEFAULT_DIR, extension:str = '.lng', pattern:dict = {}, logger:logging.Logger = None):
        # Languages instance initialization
        
        if logger is None:
            self.log = logging.getLogger("Languages")
            self.log.addHandler(logging.NullHandler())
        else:
            self.log = logger.getChild("Languages")

        self.log.debug("--- Languages initialization ---")
        
        self._pattern = pattern
        self._supported_languages = []
        
        if directory.is_dir():
            for file in directory.iterdir():
                if file.is_file() and (file.suffix.lower() == extension.lower()):
                    self.add(file)
        else:
            self.log.warning(f"{directory} is not a proper directory.")
      
    def __getitem__(self, key:str) -> dict:
        # Implementation evaluation of self[key]
        lang = str(key).lower()[:2]
        if len(key) > 2:
            country = str(key).lower()[-2:]
        else:
            country = "no_country"
        if lang in self.supported_languages_iso639:
            eligible_languages = [languages for languages in self._supported_languages if lang == languages.header['language'].lower()]
            if len(eligible_languages) > 0:
                language = eligible_languages[0]
                if country in self.supported_countries_iso3166(lang):
                    return language.all_translations[country]
                else:
                    return language.all_translations[language.default_country]
        raise KeyError(f"{lang} is not a supported language.")
    
    @property
    def supported_languages_iso639(self) -> tuple:
        # Tuple of 2-character strings representing the supported languages, following the [ISO 639.1 standard](https://www.iso.org/iso-639-language-code). **Read-only**.
        return tuple([language.header['language'].lower() for language in self._supported_languages])
    
    
    def add(self, lng_file:Path|str):
        """
        Adds a new language file.
        
        The file is checked before loading, so that only compatible language files are integrated. Once a pattern has been defined, it is used to retrieve the necessary translations.
        
        Parameters:
            lng_file:
                The file or string from which data will be imported. The file can be a pathlib.Path object, or a string describing the relative or absolute path to the file to be imported. It can also be a string containing text in [TOML format](https://toml.io).
        
        Returns:
            None
        """
        try:
            language = Language(lng_file, self._pattern, self.log)
        except FileNotFoundError:
            self.log.warning(f"{lng_file} file was not found.")
        except ValueError:
            self.log.warning(f"{lng_file} file cannot be properly decoded.")
        except TypeError:
            self.log.warning(f"{lng_file} is neither a string nor a `Path` object.")
        else:
            if language.usable:
                self._supported_languages.append(language)
                self.log.info(f"Language '{language.header['language']}' is properly supported, with the following variation(s): {language.countries}.")
            else:
                self.log.warning(f"{lang_file} file is decoded, but not usable.")
    
    def remove(self, lng:str):
        """
        Removes a language previously added.
        
        If the given language is not included in the instance, the function is silently ignored. Please notice that all countries of the language are removed too.
        
        Parameters:
            lng:
                2-character string representing the language supported by the imported file, following the [ISO 639.1 standard](https://www.iso.org/iso-639-language-code)
        
        Returns:
            None
        """
        if lng.lower() in self.supported_languages_iso639:
            for language in [languages for languages in self._supported_languages if languages.header['language'].lower() == lng.lower()]:
                try:
                    self._supported_languages.remove(language)
                except ValueError:
                    self.log.debug(f"{lng.lower()} present in `supported_languages_iso639` but there is no corresponding Language object")
                    return
            self.log.debug(f"{lng.lower()} successfully removed.")
        else:
            self.log.debug(f"No {lng.lower()} language found: removal is not possible.")

    
    def supported_countries_iso3166(self, language_iso639:str) -> tuple:
        """
        Provides all countries covered by the given language.
        
        If the given language is not supported, the returned tuple is empty.
        
        Parameters:
            language_iso639:
                2-character string representing the language supported by the imported file, following the [ISO 639.1 standard](https://www.iso.org/iso-639-language-code)
        
        Returns:
            Tuple of all countries covered by the language, represented by a 2-character string following the [ISO 3166 alpha-2 standard](https://www.iso.org/iso-3166-country-codes.html)
        """
        if language_iso639.lower() in self.supported_languages_iso639:
            for language in self._supported_languages:
                if language.header['language'].lower() == language_iso639.lower():
                    return language.countries
        return tuple()