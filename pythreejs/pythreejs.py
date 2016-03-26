r"""
Python widgets for three.js plotting

In this wrapping of three.js, we try to stay close to the three.js API.  Often, the three.js documentation at http://threejs.org/docs/ helps in understanding these classes and the various constants.  This is meant to be a low-level wrapper around three.js.  We hope that others will use this foundation to build higher-level interfaces to build 3d plots.

Another resource to understanding three.js decisions is the Udacity course on 3d graphics using three.js: https://www.udacity.com/course/cs291
"""

from ipywidgets import Widget, DOMWidget, widget_serialization
from traitlets import (Unicode, Int, Instance, Enum, List, Dict, Float,
                       Any, CFloat, Bool, This, CInt, TraitType)
from math import pi, sqrt

def vector3(trait_type=CFloat, default=None, **kwargs):
    if default is None:
        default=[0, 0, 0]
    return List(trait_type, default_value=default, minlen=3, maxlen=3, **kwargs)

def vector2(trait_type=CFloat, default=None, **kwargs):
    if default is None:
        default=[0, 0]
    return List(trait_type, default_value=default, minlen=2, maxlen=2, **kwargs)


# python 3 compatibility stuff
# http://www.voidspace.org.uk/python/articles/porting-mock-to-python-3.shtml
try:
    unicode
except NameError:
    # Python 3
    basestring = unicode = str


class Color(TraitType):
    """A color trait.

    This takes a color represented as:

    * a string of the form ``'rgb(255, 0, 0)'``, ``'rgb(100%, 0%, 0%)'``, ``'#ff0000'``, ``'#f00'``, or a color name (see the THREE.ColorKeywords listing at https://github.com/mrdoob/three.js/blob/master/src/math/Color.js)
    * an rgb tuple/list of numbers, each between 0 and 1
    * an integer (or hex value)
    """
    default_value = 'black'
    info_text = 'a color as an rgb tuple, an integer, or a string'

    def validate(self, obj, value):
        if isinstance(value, (tuple, list)) and len(value)==3:
            return 'rgb(%d,%d,%d)'%(int(value[0]), int(value[1]), int(value[2]))
        elif isinstance(value, basestring):
            # from https://github.com/mrdoob/three.js/blob/master/src/math/Color.js
            # there are lots of color names, as well as things like
            # rgb(?,?,?), rgb(?%,?%,?%), #XXXXXX, #XXX
            # TODO: validate one of those patterns, or just pass the buck to three.js
            return value
        else:
            try:
                return int(value)
            except:
                pass
        self.error(obj, value)


class Texture(Widget):
    _view_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _view_name = Unicode('TextureView').tag(sync=True)


class ImageTexture(Texture):
    """An image texture.

    The imageuri can be a data url or a web url.
    """
    _view_name = Unicode('ImageTextureView').tag(sync=True)
    imageuri = Unicode().tag(sync=True)


class DataTexture(Texture):
    """A data-based texture.

    See http://threejs.org/docs/#Reference/Textures/DataTexture.
    """
    _view_name = Unicode('DataTextureView').tag(sync=True)
    data = List(CInt).tag(sync=True)
    format = Enum(['RGBAFormat', 'AlphaFormat', 'RGBFormat', 'LuminanceFormat', 'LuminanceAlphaFormat'],
            'RGBAFormat').tag(sync=True)
    width = CInt(256).tag(sync=True)
    height = CInt(256).tag(sync=True)
    type = Enum(['UnsignedByteType', 'ByteType', 'ShortType', 'UnsignedShortType', 'IntType',
                 'UnsignedIntType', 'FloatType', 'UnsignedShort4444Type', 'UnsignedShort5551Type',
                 'UnsignedShort565Type'], 'UnsignedByteType').tag(sync=True)
    mapping = Enum(['UVMapping', 'CubeReflectionMapping', 'CubeRefractionMapping', 'SphericalReflectionMapping',
                    'SphericalRefractionMapping'], 'UVMapping').tag(sync=True)
    wrapS = Enum(['ClampToEdgeWrapping', 'RepeatWrapping', 'MirroredRepeatWrapping'], 'ClampToEdgeWrapping').tag(sync=True)
    wrapT = Enum(['ClampToEdgeWrapping', 'RepeatWrapping', 'MirroredRepeatWrapping'], 'ClampToEdgeWrapping').tag(sync=True)
    magFilter = Enum(['LinearFilter', 'NearestFilter'], 'LinearFilter').tag(sync=True)
    minFilter = Enum(['NearestFilter', 'NearestMipMapNearestFilter', 'NearestMipMapLinearFilter',
                      'LinearFilter', 'LinearMipMapNearestFilter'], 'NearestFilter').tag(sync=True)
    anisotropy = CInt(1).tag(sync=True)


class TextTexture(Texture):
    _view_name = Unicode('TextTextureView').tag(sync=True)
    fontFace = Unicode('Arial').tag(sync=True)
    size = CInt(12).tag(sync=True)
    color = Color('black').tag(sync=True)
    string = Unicode(sync=True)
    squareTexture = Bool(True).tag(sync=True)


class Object3d(Widget):
    """
    If matrix is not None, it overrides the position, rotation, scale, and up variables.
    """
    _view_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _view_name = Unicode('Object3dView').tag(sync=True)
    _model_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _model_name = Unicode('Object3dModel').tag(sync=True)
    position = vector3(CFloat).tag(sync=True)
    quaternion = List(CFloat).tag(sync=True) # [x,y,z,w]
    scale = vector3(CFloat, [1, 1, 1]).tag(sync=True)
    up = vector3(CFloat, [0, 1, 0]).tag(sync=True)
    visible = Bool(True).tag(sync=True)
    castShadow = Bool(sync=True)
    receiveShadow = Bool(sync=True)
    # FYI, this matrix has the translation in the 4th row, which is is the
    # transpose of Sage's transformation matrices
    # TODO: figure out how to get a list of instances of Object3d
    children = List().tag(sync=True, **widget_serialization)

    def set_matrix(self, m):
        self.position = m[12:15]
        x = m[0:3]
        y = m[4:7]
        z = m[8:11]
        self.scale = [self.vector_length(x),
                        self.vector_length(y),
                        self.vector_length(z)]
        m=[]
        m.extend(x)
        m.extend(y)
        m.extend(z)
        self.quaternion_from_rotation(m)
        return self

    def quaternion_from_rotation(self, m):
        """
        m is a 3 by 3 matrix, as a list of rows.  The columns of this matrix are
        the vectors x, y, and z
        """
        #x = self.normalize(m[0:3])
        #y = self.normalize(m[3:6])
        #z = self.normalize(m[6:9])
        x = m[0:3]
        y = m[3:6]
        z = m[6:9]
        trace = x[0]+y[1]+z[2]
        if (trace>0):
            s = 0.5/sqrt(trace+1)
            self.quaternion = [(y[2]-z[1])*s, (z[0]-x[2])*s, (x[1]-y[0])*s, 0.25/s]
        elif (x[0]>y[1] and x[0]>z[2]):
            s = 2.0*sqrt(1.0+x[0]-y[1]-z[2])
            self.quaternion = [0.25*s, (y[0]+x[1])/s, (z[0]+x[2])/s, (y[2]-z[1])/s]
        elif (y[1]>z[2]):
            s = 2.0*sqrt(1.0+y[1]-x[0]-z[2])
            self.quaternion = [(y[0]+x[1])/s, 0.25*s, (z[1]+y[2])/s, (z[0]-x[2])/s]
        else:
            s = 2.0*sqrt(1.0+z[2]-x[0]-y[1])
            self.quaternion = [(z[0]+x[2])/s, (z[1]+y[2])/s, 0.25*s, (x[1]-y[0])/s]

    def vector_length(self, x):
        return sqrt(x[0] * x[0] + x[1] * x[1] + x[2] * x[2])

    def vector_divide_scalar(self, scalar, x):
        if (scalar != 0):
            x[0] = x[0] / scalar
            x[1] = x[1] / scalar
            x[2] = x[2] / scalar
        else:
            x[0] = 0
            x[1] = 0
            x[2] = 0
        return x

    def normalize(self, x):
        return self.vector_divide_scalar(self.vector_length(x),x)

    def vector_cross(self, x, y): # x X y
        return [x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0]]

    def look_at(self, eye, target):
        z = self.normalize([eye[0]-target[0], eye[1]-target[1], eye[2]-target[2]]) # eye - target

        if (self.vector_length(z)==0):
            z[2]=1
        x = self.normalize(self.vector_cross(self.up, z))

        if (self.vector_length(x)==0):
            z[0] += 0.0001
            x = self.normalize(self.vector_cross(self.up, z))

        y = self.vector_cross(z, x)
        m=[]
        m.extend(x)
        m.extend(y)
        m.extend(z)
        self.quaternion_from_rotation(m)


class ScaledObject(Object3d):
    """
    This object's matrix will be scaled every time the camera is adjusted, so that the object is always the same
    size in the viewport.

    The idea is that it is the parent for objects you want to maintain the same scale.
    """
    _view_name = Unicode('ScaledObjectView').tag(sync=True)


class Controls(Widget):
    _view_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _view_name = Unicode('ControlsView').tag(sync=True)
    _model_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _model_name = Unicode('ControlsModel').tag(sync=True)
    controlling = Instance(Object3d, allow_none=True).tag(sync=True, **widget_serialization)


class OrbitControls(Controls):
    _view_name = Unicode('OrbitControlsView').tag(sync=True)
    target = vector3(CFloat).tag(sync=True)


class TrackballControls(Controls):
    _view_name = Unicode('TrackballControlsView').tag(sync=True)
    target = vector3(CFloat).tag(sync=True)


class FlyControls(Controls):
    _view_name = Unicode('FlyControlsView').tag(sync=True)

    forward_speed = Float().tag(sync=True)
    lateral_speed = Float().tag(sync=True)
    upward_speed = Float().tag(sync=True)
    roll = Float().tag(sync=True)
    pitch = Float().tag(sync=True)
    yaw = Float().tag(sync=True)


class Picker(Controls):
    _view_name  = Unicode('PickerView').tag(sync=True)
    _model_name  = Unicode('PickerModel').tag(sync=True)
    event = Unicode('click').tag(sync=True)
    root = Instance(Object3d, allow_none=True).tag(sync=True, **widget_serialization)
    picked = List(Dict).tag(sync=True)
    distance = CFloat().tag(sync=True)
    point = vector3(CFloat).tag(sync=True)
    object = Instance(Object3d, allow_none=True).tag(sync=True, **widget_serialization)
    face = vector3(CInt).tag(sync=True)
    faceNormal = vector3(CFloat).tag(sync=True)
    faceVertices = List(vector3()).tag(sync=True)
    faceIndex = CInt(sync=True)
    all = Bool(sync=True)


class Geometry(Widget):
    _view_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _view_name = Unicode('GeometryView').tag(sync=True)


class PlainGeometry(Geometry):
    _view_name = Unicode('PlainGeometryView').tag(sync=True)
    vertices = List(vector3(CFloat)).tag(sync=True)
    colors = List(Color).tag(sync=True)
    faces = List(List(CFloat)).tag(sync=True)
    # todo: faceVertexUvs = List(vector3(vector2(CFloat))).tag(sync=True)


class SphereGeometry(Geometry):
    _view_name = Unicode('SphereGeometryView').tag(sync=True)
    radius = CFloat(1).tag(sync=True)


class CylinderGeometry(Geometry):
    _view_name = Unicode('CylinderGeometryView').tag(sync=True)
    radiusTop = CFloat(1).tag(sync=True)
    radiusBottom = CFloat(1).tag(sync=True)
    height = CFloat(1).tag(sync=True)
    radiusSegments = CFloat(20).tag(sync=True)
    heightSegments = CFloat(1).tag(sync=True)
    openEnded = Bool(sync=True)


class BoxGeometry(Geometry):
    _view_name = Unicode('BoxGeometryView').tag(sync=True)
    width = CFloat(1).tag(sync=True)
    height = CFloat(1).tag(sync=True)
    depth = CFloat(1).tag(sync=True)
    widthSegments = CFloat(1).tag(sync=True)
    heightSegments = CFloat(1).tag(sync=True)
    depthSegments = CFloat(1).tag(sync=True)


class CircleGeometry(Geometry):
    _view_name = Unicode('CircleGeometryView').tag(sync=True)
    radius = CFloat(1).tag(sync=True)
    segments = CFloat(8).tag(sync=True)
    thetaStart = CFloat(0).tag(sync=True)
    thetaLength = CFloat(2*pi).tag(sync=True)


class LatheGeometry(Geometry):
    _view_name = Unicode('LatheGeometryView').tag(sync=True)
    points = List(vector3()).tag(sync=True)
    segments = CInt(12).tag(sync=True)
    phiStart = CFloat(0).tag(sync=True)
    phiLength = CFloat(2*pi).tag(sync=True)


class TubeGeometry(Geometry):
    _view_name = Unicode('TubeGeometryView').tag(sync=True)
    path = List(vector3()).tag(sync=True)
    segments = CInt(64).tag(sync=True)
    radius = CFloat(1).tag(sync=True)
    radialSegments = CFloat(8).tag(sync=True)
    closed = Bool(sync=True)


class IcosahedronGeometry(Geometry):
    _view_name = Unicode('IcosahedronGeometryView').tag(sync=True)
    radius = CFloat(1).tag(sync=True)
    detail = CFloat(0).tag(sync=True)


class OctahedronGeometry(Geometry):
    _view_name = Unicode('OctahedronGeometryView').tag(sync=True)
    radius = CFloat(1).tag(sync=True)
    detail = CFloat(0).tag(sync=True)


class PlaneGeometry(Geometry):
    _view_name = Unicode('PlaneGeometryView').tag(sync=True)
    width = CFloat(1).tag(sync=True)
    height = CFloat(1).tag(sync=True)
    widthSegments = CFloat(1).tag(sync=True)
    heightSegments = CFloat(1).tag(sync=True)


class TetrahedronGeometry(Geometry):
    _view_name = Unicode('TetrahedronGeometryView').tag(sync=True)
    radius = CFloat(1).tag(sync=True)
    detail = CFloat(0).tag(sync=True)


class TorusGeometry(Geometry):
    _view_name = Unicode('TorusGeometryView').tag(sync=True)
    radius = CFloat(1).tag(sync=True)
    tube = CFloat(1).tag(sync=True)
    radialSegments = CFloat(1).tag(sync=True)
    tubularSegments = CFloat(1).tag(sync=True)
    arc = CFloat(pi*2).tag(sync=True)


class TorusKnotGeometry(Geometry):
    _view_name = Unicode('TorusKnotGeometryView').tag(sync=True)
    radius = CFloat(1).tag(sync=True)
    tube = CFloat(1).tag(sync=True)
    radialSegments = CFloat(10).tag(sync=True)
    tubularSegments = CFloat(10).tag(sync=True)
    p = CFloat(2).tag(sync=True)
    q = CFloat(3).tag(sync=True)
    heightScale = CFloat(1).tag(sync=True)


class PolyhedronGeometry(Geometry):
    _view_name = Unicode('PolyhedronGeometryView').tag(sync=True)
    radius = CFloat(1).tag(sync=True)
    detail = CInt(0).tag(sync=True)
    vertices = List(List(CFloat)).tag(sync=True)
    faces = List(List(CInt)).tag(sync=True)


class RingGeometry(Geometry):
    _view_name = Unicode('RingGeometryView').tag(sync=True)
    innerRadius = CFloat(1.0).tag(sync=True)
    outerRadius = CFloat(3.0).tag(sync=True)
    thetaSegments = CInt(8).tag(sync=True)
    phiSegments = CInt(8).tag(sync=True)
    thetaStart = CFloat(0).tag(sync=True)
    thetaLength = CFloat(pi*2).tag(sync=True)


class SurfaceGeometry(Geometry):
    """
    A regular grid with heights
    """
    _view_name = Unicode('SurfaceGeometryView').tag(sync=True)
    z = List(CFloat, [0]*100).tag(sync=True)
    width = CInt(10).tag(sync=True)
    height = CInt(10).tag(sync=True)
    width_segments = CInt(10).tag(sync=True)
    height_segments = CInt(10).tag(sync=True)


class FaceGeometry(Geometry):
    """
    List of vertices and faces
    """
    _view_name = Unicode('FaceGeometryView').tag(sync=True)
    vertices = List(CFloat).tag(sync=True)  # [x0, y0, z0, x1, y1, z1, x2, y2, z2, ...]
    face3 = List(CInt).tag(sync=True)  # [v0,v1,v2, v0,v1,v2, v0,v1,v2, ...]
    face4 = List(CInt).tag(sync=True)  # [v0,v1,v2,v3, v0,v1,v2,v3, v0,v1,v2,v3, ...]
    facen = List(List(CInt)).tag(sync=True)  # [[v0,v1,v2,...,vn], [v0,v1,v2,...,vn], [v0,v1,v2,...,vn], ...]


class ParametricGeometry(Geometry):
    _view_name = Unicode('ParametricGeometryView').tag(sync=True)
    func = Unicode(sync=True)
    slices = CInt(105).tag(sync=True)
    stacks = CInt(105,sync=True)


class Material(Widget):
    _view_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _view_name = Unicode('MaterialView').tag(sync=True)
    # id = TODO
    name = Unicode(sync=True)
    side = Enum(['FrontSide', 'BackSide', 'DoubleSide'], 'DoubleSide').tag(sync=True)
    opacity = CFloat(1.0).tag(sync=True)
    transparent = Bool(sync=True)
    blending = Enum(['NoBlending', 'NormalBlending', 'AdditiveBlending', 'SubtractiveBlending', 'MultiplyBlending',
                    'CustomBlending'], 'NormalBlending').tag(sync=True)
    blendSrc = Enum(['ZeroFactor', 'OneFactor', 'SrcColorFactor', 'OneMinusSrcColorFactor', 'SrcAlphaFactor',
                    'OneMinusSrcAlphaFactor', 'DstAlphaFactor', 'OneMinusDstAlphaFactor'], 'SrcAlphaFactor').tag(sync=True)
    blendDst = Enum(['DstColorFactor', 'OneMinusDstColorFactor', 'SrcAlphaSaturateFactor'], 'OneMinusDstColorFactor').tag(sync=True)
    blendEquation = Enum(['AddEquation', 'SubtractEquation', 'ReverseSubtractEquation'], 'AddEquation').tag(sync=True)
    depthTest = Bool(True).tag(sync=True)
    depthWrite = Bool(True).tag(sync=True)
    polygonOffset = Bool(True).tag(sync=True)
    polygonOffsetFactor = CFloat(1.0).tag(sync=True)
    polygonOffsetUnits = CFloat(1.0).tag(sync=True)
    alphaTest = CFloat(1.0).tag(sync=True)
    overdraw = CFloat(1.0).tag(sync=True)
    visible = Bool(True).tag(sync=True)
    needsUpdate = Bool(True).tag(sync=True)


class BasicMaterial(Material):
    _view_name = Unicode('BasicMaterialView').tag(sync=True)
    _model_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _model_name = Unicode('BasicMaterialModel').tag(sync=True)
    color = Color('white').tag(sync=True)
    wireframe = Bool(sync=True)
    wireframeLinewidth = CFloat(1.0).tag(sync=True)
    wireframeLinecap = Unicode('round').tag(sync=True)
    wireframeLinejoin = Unicode('round').tag(sync=True)
    shading = Enum(['SmoothShading', 'FlatShading', 'NoShading'], 'SmoothShading').tag(sync=True)
    vertexColors = Enum(['NoColors', 'FaceColors', 'VertexColors'], 'NoColors').tag(sync=True)
    fog = Bool(sync=True)
    map = Instance(Texture, allow_none=True).tag(sync=True, **widget_serialization)
    lightMap = Instance(Texture, allow_none=True).tag(sync=True, **widget_serialization)
    specularMap = Instance(Texture, allow_none=True).tag(sync=True, **widget_serialization)
    envMap = Instance(Texture, allow_none=True).tag(sync=True, **widget_serialization)
    skinning = Bool(sync=True)
    morphTargets = Bool(sync=True)


class LambertMaterial(BasicMaterial):
    _view_name = Unicode('LambertMaterialView').tag(sync=True)
    ambient = Color('white').tag(sync=True)
    emissive = Color('black').tag(sync=True)
    reflectivity = CFloat(1.0).tag(sync=True)
    refractionRatio = CFloat(0.98).tag(sync=True)
    combine = Enum(['MultiplyOperation', 'MixOperation', 'AddOperation'], 'MultiplyOperation').tag(sync=True)


class PhongMaterial(BasicMaterial):
    _view_name = Unicode('PhongMaterialView').tag(sync=True)
    ambient = Color('white').tag(sync=True)
    emissive = Color('black').tag(sync=True)
    specular = Color('darkgray').tag(sync=True)
    shininess = CFloat(30).tag(sync=True)
    reflectivity = CFloat(1.0).tag(sync=True)
    refractionRatio = CFloat(0.98).tag(sync=True)
    combine = Enum(['MultiplyOperation', 'MixOperation', 'AddOperation'], 'MultiplyOperation').tag(sync=True)


class DepthMaterial(Material):
    _view_name = Unicode('DepthMaterialView').tag(sync=True)
    wireframe = Bool(sync=True)
    wireframeLinewidth = CFloat(1.0).tag(sync=True)


class _LineMaterial(Material):
    """Abstract base class for line materials"""
    _view_name = None


class LineBasicMaterial(_LineMaterial):
    _view_name = Unicode('LineBasicMaterialView').tag(sync=True)
    color = Color('white').tag(sync=True)
    linewidth = CFloat(1.0).tag(sync=True)
    linecap = Unicode('round').tag(sync=True)
    linejoin = Unicode('round').tag(sync=True)
    fog = Bool(sync=True)
    vertexColors = Enum(['NoColors', 'FaceColors', 'VertexColors'], 'NoColors').tag(sync=True)


class LineDashedMaterial(_LineMaterial):
    _view_name = Unicode('LineDashedMaterialView').tag(sync=True)
    color = Color('white').tag(sync=True)
    linewidth = CFloat(1.0).tag(sync=True)
    scale = CFloat(1.0).tag(sync=True)
    dashSize = CFloat(3.0).tag(sync=True)
    gapSize = CFloat(1.0).tag(sync=True)
    vertexColors = Enum(['NoColors', 'FaceColors', 'VertexColors'], 'NoColors').tag(sync=True)
    fog = Bool(sync=True)


class NormalMaterial(Material):
    _view_name = Unicode('NormalMaterialView').tag(sync=True)
    morphTargets = Bool(sync=True)
    shading = Enum(['SmoothShading', 'FlatShading', 'NoShading'], 'SmoothShading').tag(sync=True)
    wireframe = Bool(sync=True)
    wireframeLinewidth = CFloat(1.0).tag(sync=True)


class ParticleSystemMaterial(Material):
    _view_name = Unicode('ParticleSystemMaterialView').tag(sync=True)
    _model_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _model_name = Unicode('ParticleSystemMaterialModel').tag(sync=True)
    color = Color('yellow').tag(sync=True)
    map = Instance(Texture, allow_none=True).tag(sync=True, **widget_serialization)
    size = CFloat(1.0).tag(sync=True)
    sizeAttenuation = Bool(sync=True)
    vertexColors = Bool(sync=True)
    fog = Bool(sync=True)


class ShaderMaterial(Material):
    _view_name = Unicode('ShaderMaterialView').tag(sync=True)
    fragmentShader = Unicode('void main(){ }').tag(sync=True)
    vertexShader = Unicode('void main(){ }').tag(sync=True)
    morphTargets = Bool(sync=True)
    lights = Bool(sync=True)
    morphNormals = Bool(sync=True)
    wireframe = Bool(sync=True)
    vertexColors = Enum(['NoColors', 'FaceColors', 'VertexColors'], 'NoColors').tag(sync=True)
    skinning = Bool(sync=True)
    fog = Bool(sync=True)
    shading = Enum(['SmoothShading', 'FlatShading', 'NoShading'], 'SmoothShading').tag(sync=True)
    linewidth = CFloat(1.0).tag(sync=True)
    wireframeLinewidth = CFloat(1.0).tag(sync=True)


class SpriteMaterial(Material):
    _view_name = Unicode('SpriteMaterialView').tag(sync=True)
    _model_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _model_name = Unicode('SpriteMaterialModel').tag(sync=True)
    map = Instance(Texture, allow_none=True).tag(sync=True, **widget_serialization)
    uvScale = List(CFloat).tag(sync=True)
    sizeAttenuation = Bool(sync=True)
    color = Color('white').tag(sync=True)
    uvOffset = List(CFloat).tag(sync=True)
    fog = Bool(sync=True)
    useScreenCoordinates = Bool(sync=True)
    scaleByViewport = Bool(sync=True)
    alignment = List(CFloat).tag(sync=True)


class Sprite(Object3d):
    _view_name = Unicode('SpriteView').tag(sync=True)
    _model_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _model_name = Unicode('SpriteModel').tag(sync=True)
    material = Instance(Material, allow_none=True).tag(sync=True, **widget_serialization)
    scaleToTexture = Bool(sync=True)


class Mesh(Object3d):
    _view_name = Unicode('MeshView').tag(sync=True)
    _model_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _model_name = Unicode('MeshModel').tag(sync=True)
    geometry = Instance(Geometry).tag(sync=True, **widget_serialization)
    material = Instance(Material).tag(sync=True, **widget_serialization)


class Line(Mesh):
    # don't need a custom model since we aren't introducing new custom serialized properties,
    # just making the material property a more specific instance
    _view_name = Unicode('LineView').tag(sync=True)
    type = Enum(['LineStrip', 'LinePieces'], 'LineStrip').tag(sync=True)
    material = Instance(_LineMaterial).tag(sync=True, **widget_serialization)


class PlotMesh(Mesh):
    plot = Instance('sage.plot.plot3d.base.Graphics3d')

    def _plot_changed(self, name, old, new):
        self.type = new.scenetree_json()['type']
        if (self.type == 'object'):
            self.type = new.scenetree_json()['geometry']['type']
            self.material = self.material_from_object(new)
        else:
            self.type = new.scenetree_json()['children'][0]['geometry']['type']
            self.material = self.material_from_other(new)
        if(self.type == 'index_face_set'):
            self.geometry = self.geometry_from_plot(new)
        elif(self.type == 'sphere'):
            self.geometry = self.geometry_from_sphere(new)
        elif(self.type == 'box'):
            self.geometry = self.geometry_from_box(new)

    def material_from_object(self, p):
        # TODO: do this without scenetree_json()
        t = p.texture.scenetree_json()
        m = LambertMaterial(side='DoubleSide')
        m.color = t['color']
        m.opacity = t['opacity']
        # TODO: support other attributes
        return m

    def material_from_other(self, p):
        # TODO: do this without scenetree_json()
        t = p.scenetree_json()['children'][0]['texture']
        m = LambertMaterial(side='DoubleSide')
        m.color = t['color']
        m.opacity = t['opacity']
        # TODO: support other attributes
        return m

    def geometry_from_box(self, p):
        g = BoxGeometry()
        g.width = p.scenetree_json()['geometry']['size'][0]
        g.height = p.scenetree_json()['geometry']['size'][1]
        g.depth = p.scenetree_json()['geometry']['size'][2]
        return g

    def geometry_from_sphere(self, p):
        g = SphereGeometry()
        g.radius = p.scenetree_json()['children'][0]['geometry']['radius']
        return g

    def geometry_from_plot(self, p):
        from itertools import groupby, chain
        def flatten(ll):
            return list(chain.from_iterable(ll))
        p.triangulate()

        g = FaceGeometry()
        g.vertices = flatten(p.vertices())
        f = p.index_faces()
        f.sort(key=len)
        faces = {k:flatten(v) for k, v in groupby(f,len)}
        g.face3 = faces.get(3,[])
        g.face4 = faces.get(4,[])
        return g


class Camera(Object3d):
    _view_name = Unicode('CameraView').tag(sync=True)


class PerspectiveCamera(Camera):
    _view_name = Unicode('PerspectiveCameraView').tag(sync=True)
    fov = CFloat(50.0).tag(sync=True)
    aspect = CFloat(6.0 / 4.0).tag(sync=True)
    near = CFloat(0.1).tag(sync=True)
    far = CFloat(2000.0).tag(sync=True)


class OrthographicCamera(Camera):
    _view_name = Unicode('OrthographicCameraView').tag(sync=True)
    left = CFloat(-10.0).tag(sync=True)
    right = CFloat(10.0).tag(sync=True)
    top = CFloat(-10.0).tag(sync=True)
    bottom = CFloat(10.0).tag(sync=True)
    near = CFloat(0.1).tag(sync=True)
    far = CFloat(2000.0).tag(sync=True)


class Scene(Object3d):
    _view_name = Unicode('SceneView').tag(sync=True)


class Effect(Widget):
    _view_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)


class AnaglyphEffect(Effect):
    _view_name = Unicode('AnaglyphEffectView').tag(sync=True)


class Renderer(Widget):
    _view_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _view_name = Unicode('RendererView').tag(sync=True)
    _model_module = Unicode('nbextensions/pythreejs/pythreejs').tag(sync=True)
    _model_name = Unicode('RendererModel').tag(sync=True)
    width = CInt(600).tag(sync=True)
    height = CInt(400).tag(sync=True)
    renderer_type = Enum(['webgl', 'canvas', 'auto'], 'auto').tag(sync=True)
    scene = Instance(Scene).tag(sync=True, **widget_serialization)
    camera = Instance(Camera).tag(sync=True, **widget_serialization)
    controls = List(Instance(Controls)).tag(sync=True, **widget_serialization)
    effect = Instance(Effect, allow_none=True).tag(sync=True, **widget_serialization)
    background = Color('black', allow_none=True).tag(sync=True)


class Light(Object3d):
    color = Color('white').tag(sync=True) # could be string or number or tuple


class AmbientLight(Light):
    _view_name = Unicode('AmbientLight').tag(sync=True)


class IntensityLight(Light):
    _view_name = Unicode('PositionLight').tag(sync=True)
    intensity = CFloat(1).tag(sync=True)


class HemisphereLight(IntensityLight):
    _view_name = Unicode('HemisphereLight').tag(sync=True)
    ground_color = Color('blue').tag(sync=True) # could be string, number, or RGB tuple


class DirectionalLight(IntensityLight):
    _view_name = Unicode('DirectionalLight').tag(sync=True)


class PointLight(IntensityLight):
    _view_name = Unicode('PointLight').tag(sync=True)
    distance = CFloat(10).tag(sync=True)


class SpotLight(PointLight):
    _view_name = Unicode('SpotLight').tag(sync=True)
    angle = CFloat(10).tag(sync=True)
    exponent = CFloat(0.5).tag(sync=True)


# Some helper classes and functions
def lights_color():
    return [
        AmbientLight(color=(0.312, 0.188, 0.4)),
        DirectionalLight(position=[1, 0, 1], color=[0.8, 0, 0]),
        DirectionalLight(position=[1, 1, 1], color=[0, 0.8, 0]),
        DirectionalLight(position=[0, 1, 1], color=[0, 0, 0.8]),
        DirectionalLight(position=[-1, -1, -1], color=[.9,.7,.9]),
    ]


def lights_gray():
    return [
        AmbientLight(color=[.6, .6, .6]),
        DirectionalLight(position=[0, 1, 1], color=[.5, .5, .5]),
        DirectionalLight(position=[0, 0, 1], color=[.5, .5, .5]),
        DirectionalLight(position=[1, 1, 1], color=[.5, .5, .5]),
        DirectionalLight(position=[-1, -1, -1], color=[.7,.7,.7]),
    ]


class SurfaceGrid(Mesh):
    """A grid covering a surface.

    This will draw a line mesh overlaying the SurfaceGeometry.
    """
    # don't need a custom model since we aren't introducing new custom serialized properties,
    # just making some properties more specific instances
    _view_name = Unicode('SurfaceGridView').tag(sync=True)
    geometry = Instance(SurfaceGeometry).tag(sync=True, **widget_serialization)
    material = Instance(_LineMaterial).tag(sync=True, **widget_serialization)


def make_text(text, position=(0,0,0), height=1):
    """
    Return a text object at the specified location with a given height
    """
    sm = SpriteMaterial(map=TextTexture(string=text, color='white', size=100, squareTexture=False))
    return Sprite(material=sm, position = position, scaleToTexture=True, scale=[1,height,1])

def height_texture(z, colormap = 'YlGnBu_r'):
    """Create a texture corresponding to the heights in z and the given colormap."""
    from matplotlib import cm
    from skimage import img_as_ubyte
    import numpy as np

    colormap = cm.get_cmap(colormap)
    im = z.copy()
    # rescale to be in [0,1], scale nan to be the smallest value
    im -= np.nanmin(im)
    im /= np.nanmax(im)
    im = np.nan_to_num(im)

    import warnings
    with warnings.catch_warnings():
        # ignore the precision warning that comes from converting floats to uint8 types
        warnings.filterwarnings("ignore",
                                message="Possible precision loss when converting from",
                                category=UserWarning,
                                module="skimage.util.dtype")
        rgba_im = img_as_ubyte(colormap(im)) # convert the values to rgba image using the colormap

    rgba_list = list(rgba_im.flat) # make a flat list

    return DataTexture(data=rgba_list, format='RGBAFormat', width=z.shape[1], height=z.shape[0])
