import Vue from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';

import { library } from '@fortawesome/fontawesome-svg-core';
import {
  faTimesCircle,
  faUserAstronaut,
  faRobot,
  faChevronLeft,
  faCaretUp,
  faCaretDown,
  faLightbulb,
  faSearch,
  faQuestionCircle,
  faPaperPlane,
  faDna,
  faDownload,
  faRedo
} from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

library.add(
  faTimesCircle,
  faUserAstronaut,
  faRobot,
  faChevronLeft,
  faCaretUp,
  faCaretDown,
  faLightbulb,
  faSearch,
  faQuestionCircle,
  faPaperPlane,
  faDna,
  faDownload,
  faRedo
);

Vue.component('font-awesome-icon', FontAwesomeIcon);

Vue.config.productionTip = false;

new Vue({
  router,
  store,
  render: (h) => h(App)
}).$mount('#app');
