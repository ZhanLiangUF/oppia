// Copyright 2014 The Oppia Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Unit tests for text input validation service.
 */

import { TestBed } from '@angular/core/testing';

import { AnswerGroup, AnswerGroupObjectFactory } from 'domain/exploration/AnswerGroupObjectFactory';
import { AppConstants } from 'app.constants';
import { InteractionSpecsConstants } from 'pages/interaction-specs.constants';
import { Outcome, OutcomeObjectFactory } from 'domain/exploration/OutcomeObjectFactory';
import { Rule, RuleObjectFactory } from 'domain/exploration/RuleObjectFactory';
import { SubtitledUnicode } from 'domain/exploration/SubtitledUnicodeObjectFactory';
import { TextInputValidationService, Validators } from 'interactions/TextInput/directives/text-input-validation.service';
import { TextInputCustomizationArgs } from 'interactions/customization-args-defs';

describe('TextInputValidationService', () => {
  let validatorService: TextInputValidationService;
  let WARNING_TYPES = AppConstants.WARNING_TYPES;
  let INTERACTION_SPECS = InteractionSpecsConstants.INTERACTION_SPECS;
  // Here 'minRows' and 'maxRows' are undefined in order to test validations.
  let minRows: number | undefined;
  let maxRows: number | undefined;

  let currentState: string;
  let customizationArguments: TextInputCustomizationArgs;
  let goodAnswerGroups: AnswerGroup[];
  let goodDefaultOutcome: Outcome;
  let oof: OutcomeObjectFactory;
  let agof: AnswerGroupObjectFactory;
  let rof: RuleObjectFactory;

  let createAnswerGroupByRules: (rules: Rule[]) => AnswerGroup;

  beforeEach(() => {
    validatorService = TestBed.inject(TextInputValidationService);
    oof = TestBed.inject(OutcomeObjectFactory);
    agof = TestBed.inject(AnswerGroupObjectFactory);
    rof = TestBed.inject(RuleObjectFactory);
    WARNING_TYPES = AppConstants.WARNING_TYPES;
    let customizationArgSpecs =
     INTERACTION_SPECS.TextInput.customization_arg_specs;
    let rowsSpecs = customizationArgSpecs[1];
    const validators = <Validators[]>rowsSpecs.schema.validators;
    minRows = validators[0].min_value;
    maxRows = validators[1].max_value;

    currentState = 'First State';
    goodDefaultOutcome = oof.createFromBackendDict({
      dest: 'Second State',
      feedback: {
        html: '',
        content_id: null
      },
      labelled_as_correct: false,
      param_changes: [],
      refresher_exploration_id: null,
      missing_prerequisite_skill_id: null
    });

    customizationArguments = {
      placeholder: {
        value: new SubtitledUnicode('', '')
      },
      rows: {
        value: 1
      }
    };

    goodAnswerGroups = [agof.createNew([], goodDefaultOutcome, [], null)];
    createAnswerGroupByRules = (rules) => agof.createNew(
      rules,
      goodDefaultOutcome,
      [],
      null
    );
  });

  it('should be able to perform basic validation', () => {
    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, goodAnswerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([]);
  });

  it('should catch non-string value for placeholder', () => {
    // This throws "Type 'number' is not assignable to type 'SubtitledUnicode'".
    // We need to suppress this error because we need to test validations.
    // @ts-expect-error
    customizationArguments.placeholder.value = 1;
    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, goodAnswerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: ('Placeholder text must be a string.')
    }]);
  });

  it('should catch non-string value for placeholder', () => {
    customizationArguments.placeholder.value = (
    // This throws "Argument of type 'undefined' is not assignable to
    // parameter of type 'string'". We need to suppress this error
    // because we need to test validations.
    // @ts-ignore
      new SubtitledUnicode(undefined, undefined));
    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, goodAnswerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: ('Placeholder text must be a string.')
    }]);
  });

  it('should catch non-integer value for # rows', () => {
    customizationArguments.rows.value = 1.5;
    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, goodAnswerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: ('Number of rows must be integral.')
    }]);
  });

  it('should catch an out of range value for # rows', () => {
    customizationArguments.rows.value = -1;
    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, goodAnswerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: (
        'Number of rows must be between ' + minRows + ' and ' +
        maxRows + '.')
    }]);
  });

  it('should catch non-unique rule type within one answer group', () => {
    let answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Equals',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput'),
          rof.createFromBackendDict({
            rule_type: 'Equals',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyza']
              }
            }
          }, 'TextInput')
        ]
      )];

    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Answer group 1 has multiple rules with ' +
        'the same type \'Equals\' within the same group.'
    }]);
  });

  it('should catch redundancy of contains rules with matching inputs', () => {
    let answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Contains',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Contains',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyza']
              }
            }
          }, 'TextInput')
        ]
      )];

    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'Contains\' rule with a matching input.'
    }]);

    answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Contains',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Contains',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['abc']
              }
            }
          }, 'TextInput')
        ]
      )];

    warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'Contains\' rule with a matching input.'
    }]);

    answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Contains',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Contains',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      )];

    warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'Contains\' rule with a matching input.'
    }]);
  });

  it('should catch redundancy of startsWith rules with matching inputs', () => {
    let answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'StartsWith',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'StartsWith',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyza']
              }
            }
          }, 'TextInput')
        ]
      )];

    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'StartsWith\' rule with a matching prefix.'
    }]);

    answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'StartsWith',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'StartsWith',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['abc']
              }
            }
          }, 'TextInput')
        ]
      )];

    warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'StartsWith\' rule with a matching prefix.'
    }]);

    answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Contains',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'StartsWith',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyzy']
              }
            }
          }, 'TextInput')
        ]
      )];

    warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'StartsWith\' rule with a matching prefix.'
    }]);
  });

  it('should catch redundancy of equals rules with matching inputs', () => {
    let answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Equals',
            inputs: {
              x: {
                contentId: 'rule_input_4',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Equals',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      )];

    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'Equals\' rule with a matching input.'
    }]);

    answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'FuzzyEquals',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'Equals',
            inputs: {
              x: {
                contentId: 'rule_input_4',
                normalizedStrSet: ['xya']
              }
            }
          }, 'TextInput')
        ]
      )];

    warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'FuzzyEquals\' rule with a matching input.'
    }]);
  });

  it('should catch redundancy of fuzzyEquals rules with matching input', () => {
    let answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'FuzzyEquals',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'FuzzyEquals',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      )];

    let warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'FuzzyEquals\' rule with a matching input.'
    }]);

    answerGroups = [
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'FuzzyEquals',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xyz']
              }
            }
          }, 'TextInput')
        ]
      ),
      createAnswerGroupByRules(
        [
          rof.createFromBackendDict({
            rule_type: 'FuzzyEquals',
            inputs: {
              x: {
                contentId: 'rule_input',
                normalizedStrSet: ['xya']
              }
            }
          }, 'TextInput')
        ]
      )];

    warnings = validatorService.getAllWarnings(
      currentState, customizationArguments, answerGroups,
      goodDefaultOutcome);
    expect(warnings).toEqual([{
      type: WARNING_TYPES.ERROR,
      message: 'Rule 1 from answer group 2 will never be matched because it' +
      ' is preceded by a \'FuzzyEquals\' rule with a matching input.'
    }]);
  });
});
