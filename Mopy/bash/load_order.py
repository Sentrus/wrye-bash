# -*- coding: utf-8 -*-
#
# GPL License and Copyright Notice ============================================
#  This file is part of Wrye Bash.
#
#  Wrye Bash is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  Wrye Bash is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Wrye Bash; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#  Wrye Bash copyright (C) 2005-2009 Wrye, 2010-2014 Wrye Bash Team
#  https://github.com/wrye-bash
#
# =============================================================================
import bolt
import bush
import liblo as _liblo
import bosh

class LoadOrder(object):
    """Immutable class representing a load order."""
    __empty = ()
    __none = frozenset()

    def __init__(self, loadOrder=__empty, active=__none):
        self._loadOrder = tuple(loadOrder)
        self._active = frozenset(active)
        self.__mod_loIndex = dict((a, i) for i, a in enumerate(loadOrder))
        # sugar, client could readily compute this - API: maybe drop:
        self._activeOrdered = tuple(
            sorted(active, key=lambda x: self.__mod_loIndex[x]))

    @property
    def loadOrder(self): return self._loadOrder # test if empty
    @property
    def active(self): return self._active  # test if none
    @property # sugar
    def activeOrdered(self): return self._activeOrdered

# Module level cache
__empty = LoadOrder()
_current_lo = __empty # must always be valid (or __empty)

# liblo calls - they include fixup code (which may or may not be needed/working)
def _getLoFromLiblo():
    lord = _liblo_handle.GetLoadOrder()
    #(ut) below ripped from bosh.Plugins - STILL needed with liblo 6.0?
    # game's master might be out of place (if using timestamps for load
    # ordering or a manually edited loadorder.txt) so move it up
    masterDex = lord.index(bosh.modInfos.masterName)
    masterName = bosh.modInfos.masterName
    if masterDex > 0:
        bolt.deprint(u'%s in %d position' % (masterName, masterDex))
        lord.remove(masterName)
        lord.insert(0, masterName)
        #(ut) SHOULDN'T WE SAVE THE LO HERE ? !!!!!!
    return lord

def _updateCache():
    global _current_lo
    try:
        lord = _getLoFromLiblo()
        acti = _liblo_handle.GetActivePlugins(lo_with_corrected_master=lord)
        _current_lo = LoadOrder(lord, acti)
    except _liblo.LibloError:
        _current_lo = __empty
        raise

def GetLo(cached=False):
    if not cached or _current_lo is __empty: _updateCache()
    return list(_current_lo.loadOrder)

def GetActivePlugins(cached=False):
    if not cached or _current_lo is __empty: _updateCache()
    return list(_current_lo.activeOrdered)

def SetActivePlugins(act): _liblo_handle.SetActivePlugins(act)
def SetLoadOrder(lord): _liblo_handle.SetLoadOrder(lord)

def libloLOMismatchCallback():
    """Called whenever a mismatched loadorder.txt and plugins.txt is found"""
    # Force a rewrite of both plugins.txt and loadorder.txt
    # In other words, use what's in loadorder.txt to write plugins.txt
    # TODO: Check if this actually works. # FIXME !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # plugins is modInfos private + this is a hack + ...
    bosh.modInfos.plugins.loadLoadOrder()
    bosh.modInfos.plugins.saveLoadOrder()

#----------------------------------------------------------------------REFACTOR
_liblo.Init(bosh.dirs['compiled'].s)
# That didn't work - Wrye Bash isn't installed correctly
if not _liblo.liblo:
    raise bolt.BoltError(u'The libloadorder API could not be loaded.')
bolt.deprint(u'Using libloadorder API version:', _liblo.version)

_liblo_handle = _liblo.LibloHandle(bosh.dirs['app'].s,bush.game.fsName)
if bush.game.fsName == u'Oblivion' and bosh.dirs['mods'].join(
        u'Nehrim.esm').isfile():
    _liblo_handle.SetGameMaster(u'Nehrim.esm')
#---------------------------------------------------------------NO CALLBACKS!!!
# This warning can only occur when using libloadorder with a game that uses
# the textfile-based load order system
_liblo.RegisterCallback(_liblo.LIBLO_WARN_LO_MISMATCH, libloLOMismatchCallback)

def usingTxtFile(): return _liblo_handle.usingTxtFile()
