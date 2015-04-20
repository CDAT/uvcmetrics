#include <Python.h>
#include "numpy/ndarrayobject.h"


static PyObject *
  PyACME_apply_weights(PyObject *self,PyObject *args)
{
  PyObject *row_obj,*col_obj,*S_obj,*fracb_obj,*data_obj;
  PyArrayObject *row=NULL,*col=NULL,*S=NULL,*fracb=NULL,*dest_field=NULL,*data=NULL;
  double *S_vals,*fracb_vals;
  int *row_vals,*col_vals;
  char type;
  void *data_vals;
  double *out;

  if (!PyArg_ParseTuple(args,"OOOOO",&data_obj,&S_obj,&row_obj,&col_obj,&fracb_obj))
    return NULL;

    S =(PyArrayObject *) PyArray_ContiguousFromAny(S_obj,NPY_FLOAT64,1,1);
    col =(PyArrayObject *) PyArray_ContiguousFromAny(col_obj,NPY_INT32,1,1);
    row =(PyArrayObject *) PyArray_ContiguousFromAny(row_obj,NPY_INT32,1,1);
    data =(PyArrayObject *) PyArray_ContiguousFromAny(data_obj,NPY_NOTYPE,1,0);
    fracb =(PyArrayObject *) PyArray_ContiguousFromAny(fracb_obj,NPY_FLOAT64,1,1);

    type = data->descr->type;
    int nindep=1;
    int i,j;
    for (i=0;i<data->nd-1;i++) {
      nindep*=data->dimensions[i];
    }
    /* Construct dest array */
    int n1 = data->dimensions[data->nd-1];
    int n2 = fracb->dimensions[0];
    npy_intp newdims[2];
    newdims[0]=nindep;
    newdims[1] = n2;
    out=malloc(newdims[0]*newdims[1]*sizeof(double));
    #pragma omp parallel for
    for (j=0;j<newdims[0]*newdims[1];j++) {
      out[j]=0;
    }

    dest_field = PyArray_SimpleNew(2,newdims,NPY_DOUBLE);

    S_vals = (double *)S->data;
    row_vals = (int *) row->data;
    col_vals = (int *) col->data;
    data_vals = (void *) data->data;
    fracb_vals = (double *) fracb->data;
    #pragma omp parallel for private(j)
    for (i=0;i<nindep;i++) {
      if (type=='d') {
        for (j=0;j<S->dimensions[0];j++) {
          out[i*n2+row_vals[j]] = out[i*n2+row_vals[j]] + S_vals[j]*((double *)data_vals)[i*n1+col_vals[j]];
        }
      }
      else if (type=='f') {
        for (j=0;j<S->dimensions[0];j++) {
          out[i*n2+row_vals[j]] = out[i*n2+row_vals[j]] + S_vals[j]*((float *)data_vals)[i*n1+col_vals[j]];
        }
      }
      else if (type=='i') {
        for (j=0;j<S->dimensions[0];j++) {
          out[i*n2+row_vals[j]] = out[i*n2+row_vals[j]] + S_vals[j]*((int *)data_vals)[i*n1+col_vals[j]];
        }
      }
      else if (type=='l') {
        for (j=0;j<S->dimensions[0];j++) {
          out[i*n2+row_vals[j]] = out[i*n2+row_vals[j]] + S_vals[j]*((long *)data_vals)[i*n1+col_vals[j]];
        }
      }
      else {
        fprintf(stderr,"unsupported type: %c\n" , type);
      }
      for (j=0;j<n2;j++) {
        if (fracb_vals[j]>0.) out[i*n2+j]=out[i*n2+j]/fracb_vals[j];
      }
    }
    dest_field->data=out;
  return Py_BuildValue("N",dest_field);
}

static PyMethodDef MyExtractMethods[]= {
  {"apply_weights",PyACME_apply_weights, METH_VARARGS},
  {NULL, NULL} /*sentinel */
};

PyMODINIT_FUNC init_regrid(void)
{
  (void) Py_InitModule("_regrid", MyExtractMethods);
  import_array();
  
}

/* int main(int argc,char **argv) */
/* { */
/*   Py_SetProgramName(argv[0]); */
/*   Py_Initialize(); */
/*   init_cmor(); */
/*   return 0; */
/* } */

