
#define N_MSGS 10
typedef struct{
    char str[100];
    bool b;
} message;

void set_message(message *m, bool b){
    if(b & !m->b) rtapi_print_msg(RTAPI_MSG_ERR, m->str);    
    m->b = b;
}

void reset_messages(message m[], bool r){
    static bool br=0;
    if(r && !br) for(int i=0;i<N_MSGS;i++) m[i].b=0;
    br=r;
}

typedef struct {
        float T;
        float ET;
        bool  IN;
        bool  OUT;
} timer;

void iec_ton(timer *t, float fper){
   if(t->IN) t->ET += fper;
   else      t->ET = 0.0;
   if(t->ET >= t->T){
      t->ET = t->T;
      t->OUT = true;
   }
   else t->OUT = false;
}

void iec_tof(timer *t, float fper){
   if(t->IN) t->ET = t->T;
   else      t->ET -= fper;

   if(t->ET < 0.0)t->ET = 0.0;
   t->OUT = (t->ET > 0.0);
}

bool iec_fp(bool in, bool *m){
        bool out=in && !*m;
        *m=in;
        return out;
} //iec_fp

bool iec_fn(bool in, bool *m){
        bool out=!in && *m;
        *m=in;
        return out;
} //iec_fn


