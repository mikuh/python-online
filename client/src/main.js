import Vue from 'vue'
import App from './App.vue'
import router from './router'

// axios
import axios from 'axios'
axios.defaults.withCredentials=true; //让ajax携带cookie
Vue.prototype.$axios = axios;

// xterm
import 'xterm/dist/xterm.css'

// VueCodemirror
import VueCodemirror from 'vue-codemirror'
// require styles
import 'codemirror/lib/codemirror.css'
Vue.use(VueCodemirror, )

// VueMaterial
import VueMaterial from 'vue-material'
import 'vue-material/dist/vue-material.min.css'
Vue.use(VueMaterial)


Vue.config.productionTip = false


// new Vue({
//   render: h => h(App),
//   router,
// }).$mount('#app')
new Vue({
  el: '#app',
  router,
  render: h => h(App)
})