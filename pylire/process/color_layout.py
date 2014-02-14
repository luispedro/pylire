
import numpy
import numexpr

zigzag = numpy.array([
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5,
    12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63
], dtype="int")

cosine = numpy.array([
    [
        3.535534e-01, 3.535534e-01, 3.535534e-01, 3.535534e-01,
        3.535534e-01, 3.535534e-01, 3.535534e-01, 3.535534e-01
    ], [
        4.903926e-01, 4.157348e-01, 2.777851e-01, 9.754516e-02,
        -9.754516e-02, -2.777851e-01, -4.157348e-01, -4.903926e-01
    ], [
        4.619398e-01, 1.913417e-01, -1.913417e-01, -4.619398e-01,
        -4.619398e-01, -1.913417e-01, 1.913417e-01, 4.619398e-01
    ], [
        4.157348e-01, -9.754516e-02, -4.903926e-01, -2.777851e-01,
        2.777851e-01, 4.903926e-01, 9.754516e-02, -4.157348e-01
    ], [
        3.535534e-01, -3.535534e-01, -3.535534e-01, 3.535534e-01,
        3.535534e-01, -3.535534e-01, -3.535534e-01, 3.535534e-01
    ], [
        2.777851e-01, -4.903926e-01, 9.754516e-02, 4.157348e-01,
        -4.157348e-01, -9.754516e-02, 4.903926e-01, -2.777851e-01
    ], [
        1.913417e-01, -4.619398e-01, 4.619398e-01, -1.913417e-01,
        -1.913417e-01, 4.619398e-01, -4.619398e-01, 1.913417e-01
    ], [
        9.754516e-02, -2.777851e-01, 4.157348e-01, -4.903926e-01,
        4.903926e-01, -4.157348e-01, 2.777851e-01, -9.754516e-02
    ]
], dtype="double")

def quant_ydc(ints):
    return numexpr.evaluate("""
where(ints > 192, 112 + ((i - 192) >> 2),
where(ints > 160, 96 + ((i - 160) >> 1),
where(ints > 96, 32 + (i - 96),
where(ints > 64, 16 + ((i - 64) >> 1), 0))))""")

def quant_cdc(ints):
    return numexpr.evaluate("""
where(ints > 191, 63,
where(ints > 160, 56 + ((i - 160) >> 2),
where(ints > 144, 48 + ((i - 144) >> 1),
where(ints > 112, 16 + (i - 112),
where(ints > 96, 8 + ((i - 96) >> 1),
where(ints > 64, (i - 64) >> 2, 0))))))""")

def quant_ac(ints):
    ints = numpy.clip(ints, -256, 255)
    out = numexpr.evaluate("""
where(abs(ints) > 127, 64 + ((abs(ints)) >> 2),
where(abs(ints) > 63, 32 + ((abs(ints)) >> 2), abs(ints)
))""")
    signed = numexpr.evaluate("where(ints < 0, -1, 1)")
    return (out * signed) + 128

def create_shape_from_RGB_image(ndim):
    shape = numpy.zeros((3, 64), dtype="int")
    total = numpy.zeros((3, 64), dtype="long")
    (R, G, B) = (channel.T for channel in ndim.T)
    
