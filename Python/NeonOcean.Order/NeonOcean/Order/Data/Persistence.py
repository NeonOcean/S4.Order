import copy
import json
import os
import typing

from NeonOcean.Order import Debug, Paths, This
from NeonOcean.Order.Tools import Exceptions, Types, Version

_valueKey = "Value"
_lastChangeVersionKey = "Last Change Version"

class _Value:
	def __init__ (self, value, valueType: type, version: Version.Version, default, verify: typing.Callable):
		"""
		Used for storage of persistent data.
		"""

		self.Value = value
		self.ValueType = valueType  # type: type
		self.Version = version  # type: Version.Version
		self.Default = default
		self.Verify = verify  # type: typing.Callable

	def Save (self) -> dict:
		return {
			_valueKey: self.Value,
			_lastChangeVersionKey: str(self.Version)
		}

	def Get (self):
		return copy.deepcopy(self.Value)

	def Set (self, value, version: Version.Version) -> None:
		self.Value = copy.deepcopy(self.Verify(value, version))
		self.Version = Version.Version(str(version))

class Persistent:
	def __init__ (self, filePath: str, currentVersion: Version.Version, hostNamespace: str = This.Mod.Namespace):
		"""
		Reads, writes and stores persistent data.

		:param filePath: The file path this persistence object will be written to and read from.
		:type filePath: str
		:param currentVersion: The current version of what ever will be controlling this persistence object.
							   This value can allow you to correct outdated persistent values.
		:type currentVersion: Version.Version
		:param hostNamespace: Errors made by this persistent object will show up under this namespace.
		:type hostNamespace: str
		"""

		if not isinstance(filePath, str):
			raise Exceptions.IncorrectTypeException(filePath, "path", (str,))

		if not isinstance(currentVersion, Version.Version):
			raise Exceptions.IncorrectTypeException(currentVersion, "currentVersion", (Version.Version,))

		if not isinstance(hostNamespace, str):
			raise Exceptions.IncorrectTypeException(hostNamespace, "hostNamespace", (str,))

		self.FilePath = filePath  # type: str
		self.CurrentVersion = currentVersion  # type: Version.Version
		self.HostNamespace = hostNamespace  # type: str

		self._file = dict()  # type: typing.Dict[str, typing.Dict[str, str]]

		self._storage = dict()  # type: typing.Dict[str, _Value]
		self._updateStorage = list()  # type: list

	def Load (self) -> None:
		"""
		Load persistent data from the file path specified when initiating this object, if it exists.
		:rtype: None
		"""

		persistentData = { }  # type: dict

		if os.path.exists(self.FilePath):
			try:
				with open(self.FilePath) as persistentFile:
					persistentData = json.JSONDecoder().decode(persistentFile.read())

				if not isinstance(persistentData, dict):
					raise TypeError("Cannot convert file to dictionary.")
			except Exception as e:
				Debug.Log("Failed to read '" + Paths.StripUserDataPath(self.FilePath) + "'.", self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__, exception = e)

			changed = False

			for persistentKey in list(persistentData.keys()):  # type: str
				persistentValue = persistentData[persistentKey]

				if not isinstance(persistentKey, str):
					persistentData.pop(persistentKey, None)
					Debug.Log("Persistent data key must be '" + Types.GetFullName(str) + "' not '" + Types.GetFullName(persistentKey) + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
					changed = True
					continue

				if not isinstance(persistentValue, dict):
					persistentData.pop(persistentKey, None)
					Debug.Log("Persistent data dictionary must be '" + Types.GetFullName(dict) + "' not '" + Types.GetFullName(persistentValue) + "'. Key: '" + persistentKey + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
					changed = True
					continue

				if not _valueKey in persistentValue:
					persistentData.pop(persistentKey, None)
					Debug.Log("Persistent data has no value. Key: '" + persistentKey + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
					changed = True
					continue

				for persistentValueKey in list(persistentValue.keys()):  # type: str
					if persistentValueKey == _lastChangeVersionKey:
						persistentValueValue = persistentValue[persistentValueKey]

						if not isinstance(persistentValueValue, str):
							persistentData.pop(persistentKey, None)
							Debug.Log("Persistent last change versions must be '" + Types.GetFullName(str) + "' not '" + Types.GetFullName(persistentValueValue) + "'. Key: '" + persistentKey + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
							changed = True

						try:
							Version.Version(persistentValueValue)
						except:
							persistentData.pop(persistentKey, None)
							Debug.Log("Cannot parse '" + persistentValueValue + "' to a version object. Key: '" + persistentKey + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
							changed = True

						break

				if not _lastChangeVersionKey in persistentValue:
					persistentValue[_lastChangeVersionKey] = str(self.CurrentVersion)
					changed = True

				if not persistentKey in self._storage:
					continue

				valueStorage = self._storage[persistentKey]  # type: _Value
				valueObject = persistentValue[_valueKey]

				if not isinstance(valueObject, valueStorage.ValueType):
					Debug.Log("Persistent data for '" + persistentKey + "' is of the type '" + Types.GetFullName(valueObject) + "' and not '" + Types.GetFullName(valueStorage.ValueType) + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
					persistentData.pop(persistentKey, None)
					changed = True
					continue

				try:
					valueStorage.Set(valueObject, Version.Version(persistentValue[_lastChangeVersionKey]))
				except:
					Debug.Log("Cannot set value '" + str(persistentValue[_valueKey]) + "' for persistent data '" + persistentKey + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
					persistentData.pop(persistentKey, None)
					changed = True
					continue

			if changed:
				self.Save()

		self._file = persistentData
		self.Update()

	def Save (self) -> None:
		"""
		Saves the currently stored persistent data to the file path specified when initiating this object.
		If the directory the save file is in doesn't exist one will be created.
		:rtype: None
		"""

		saveData = copy.deepcopy(self._file)  # type: typing.Dict[str, dict]

		for storageKey, storageValue in self._storage.items():  # type: str, _Value
			try:
				saveData[storageKey] = storageValue.Save()
			except:
				Debug.Log("Failed to save value of '" + storageKey + "'. This entry may be reset the next time this persistent data is loaded.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				saveData.pop(storageKey)

		if not os.path.exists(os.path.dirname(self.FilePath)):
			os.makedirs(os.path.dirname(self.FilePath))

		with open(self.FilePath, mode = "w+") as persistentFile:
			persistentFile.write(json.JSONEncoder(indent = 4).encode(saveData))

	def Setup (self, key: str, valueType: type, default, verify: typing.Callable) -> None:
		"""
		Setup persistent data for this persistence object. All persistent data must be setup before it can be used.
		Persistent data can be loaded before being setup but will remain dormant until setup.
		Persistent data cannot be setup twice, an exception will be raised if this is tried.

		:param key: The name of the persistent data to be setup. This will be used to get and set the value in the future and is case sensitive.
		:type key: str

		:param valueType: The persistent data's value type, i.e. str, bool, float. The value of this persistent data should never be anything other than this type.
		:type valueType: type

		:param default: The persistent data's default value. Needs to be of the type specified in the valueType parameter.

		:param verify: This is called when changing or loading a value to verify that is correct and still valid.
					   Verify functions need to take two parameters: the value being verified and the version the value was set.
					   The first parameter will always be of the type specified in the 'valueType'. The value will often not be the current value of the persistent data.
					   The second parameter will be the version this value was set. The type of this parameter will be NeonOcean.Order.Tools.Version.Version
					   Verify functions should also return the input or a corrected value.
					   If the value cannot be corrected the verify function should raise an exception, the persistent data may then revert to its default if necessary.
		:type verify: typing.Callable

		:rtype: None
		"""

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if key in self._storage:
			raise Exception("Persistent data '" + key + "' is already setup.")

		if not isinstance(valueType, type):
			raise Exceptions.IncorrectTypeException(valueType, "valueType", (type,))

		if not isinstance(default, valueType):
			raise Exceptions.IncorrectTypeException(default, "default", (valueType,))

		if not isinstance(verify, typing.Callable):
			raise Exceptions.IncorrectTypeException(verify, "verify", ("Callable",))

		try:
			verifiedDefault = verify(default)
		except Exception as e:
			raise ValueError("Failed to verify default value for persistent data '" + key + "'.") from e

		if verifiedDefault != default:
			Debug.Log("Verification of default value for persistent data '" + key + "' changed it.", self.HostNamespace, level = Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)

		if key in self._file:
			data = self._file[key]  # type: dict

			dataValue = data[_valueKey]
			dataVersion = Version.Version(data[_lastChangeVersionKey])
		else:
			dataValue = None  # type: str
			dataVersion = self.CurrentVersion

		if dataValue is not None:
			try:
				value = verify(dataValue)
				version = dataVersion
			except:
				Debug.Log("Verify callback found fault with the value that was stored for persistent data '" + key + "'.", self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
				value = verifiedDefault
				version = self.CurrentVersion
		else:
			value = verifiedDefault
			version = dataVersion

		self._storage[key] = _Value(value, valueType, version, default, verify)

	def isSetup (self, key: str) -> bool:
		"""
		Returns true if the persistent data specified by parameter key is setup.

		:param key: The name of the persistent data, is case sensitive.
		:type key: str
		:rtype: bool
		"""

		if key in self._storage:
			return True
		else:
			return False
		pass

	def Get (self, key: str):
		"""
		Gets the value of the persistent data specified by parameter key. The value returned will be a deep copy of what is stored, modifying it should never change
		anything unless you set it with the set function.

		:param key: The name of the persistent data, is case sensitive.
		:type key: str
		:return: The return object will always be of the type specified for the target persistent data during setup.
		"""

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if key in self._storage:
			return self._storage[key].Get()
		else:
			raise Exception("Persistent data '" + key + "' is not setup.")

	def Set (self, key: str, value, autoSave: bool = True, autoUpdate: bool = True) -> None:
		"""
		Set the value of the persistent data specified by parameter key. The value is deep copied before being but into storage, modifying the value after setting
		it will not change the stored version.

		:param key: The name of the persistent data, is case sensitive.
		:type key: str
		:param value: The value the persistent data will be changing to. This must be of the type specified for the target persistent data during setup.
		:param autoSave: Whether or not to automatically save the persistent data after changing the value.
		 				 This can allow you to change multiple values at once without saving each time.
		:type autoSave: bool
		:param autoUpdate: Whether or not to automatically update callbacks to the fact that a value has changed.
						   This can allow you to change multiple values at once without calling update callbacks each time.
		:type autoUpdate: bool
		:rtype: None
		"""

		if not isinstance(key, str):
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if key in self._storage:
			valueStorage = self._storage[key]
		else:
			raise Exception("Persistent data '" + key + "' is not setup.")

		if not isinstance(value, valueStorage.ValueType):
			raise Exceptions.IncorrectTypeException(value, "value", (valueStorage.ValueType,))

		if not isinstance(autoSave, bool):
			raise Exceptions.IncorrectTypeException(autoSave, "autoSave", (bool,))

		if not isinstance(autoUpdate, bool):
			raise Exceptions.IncorrectTypeException(autoUpdate, "autoUpdate", (bool,))

		valueStorage.Set(value, self.CurrentVersion)

		if autoSave:
			self.Save()

		if autoUpdate:
			self.Update()

	def Reset (self, key: str = None) -> None:
		"""
		Resets persistent data to its default value.

		:param key: The name of the persistent data, is case sensitive. If the key is none, all settings will be reset.
		:type key: str
		:rtype: None
		"""

		if not isinstance(key, str) and key is not None:
			raise Exceptions.IncorrectTypeException(key, "key", (str,))

		if key is None:
			for key, value in self._storage.items():  # type: _Value
				value.Value = value.Default
		else:
			valueStorage = self._storage.get(key)  # type: _Value

			if valueStorage is not None:
				valueStorage.Value = valueStorage.Default
			else:
				raise Exception("Persistent data '" + key + "' is not setup.")

		self.Save()
		self.Update()

	def Update (self) -> None:
		"""
		Calls all update functions listening to this persistence object.
		This should be called after any persistent data change where you elected not to allow for auto-updating.

		:rtype: None
		"""

		for callback in self._updateStorage:  # type: typing.Callable
			callback()

	def RegisterUpdate (self, update: typing.Callable) -> None:
		"""
		Register an update callback function to this persistence object.
		Updates should be called any time any value is changed.

		:param update: Update callbacks must take no parameters.
		:type update: typing.Callable
		:rtype: None
		"""

		if not isinstance(update, typing.Callable):
			raise Exceptions.IncorrectTypeException(update, "update", ("Callable",))

		self._updateStorage.append(update)

	def UnregisterUpdate (self, update: typing.Callable) -> None:
		"""
		Removes a update callback from the registry.

		:param update: The callback targeted for removal.
		:type update: typing.Callable
		:rtype: None
		"""

		if not isinstance(update, typing.Callable):
			raise Exceptions.IncorrectTypeException(update, "update", ("Callable",))

		if update in self._updateStorage:
			self._updateStorage.remove(update)
