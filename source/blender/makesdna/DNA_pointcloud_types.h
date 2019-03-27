/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file DNA_pointcloud_types.h
 *  \ingroup DNA
 */

#ifndef __DNA_POINTCLOUD_TYPES_H__
#define __DNA_POINTCLOUD_TYPES_H__

#include "DNA_ID.h"
#include "DNA_customdata_types.h"

/* TODO: for compatibility with node systems and renderers, separate
 * data layers for coordinate and radius seems better? */
typedef struct Point {
  float co[3];
  float radius;
} Point;

typedef struct PointCloud {
  ID id;
  struct AnimData *adt; /* animation data (must be immediately after id) */

  int flag;
  int _pad1[1];

  /* Geometry */
  struct Point *points;
  int totpoint;
  int _pad2[1];

  /* Custom Data */
  struct CustomData pdata;

  /* Material */
  struct Material **mat;
  short totcol;
  short _pad3[3];

  /* Draw Cache */
  void *batch_cache;
} PointCloud;

/* PointCloud.flag */
enum {
  PT_DS_EXPAND = (1 << 0),
};

#endif /* __DNA_POINTCLOUD_TYPES_H__ */
